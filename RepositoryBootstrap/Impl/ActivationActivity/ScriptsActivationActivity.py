# ----------------------------------------------------------------------
# |  
# |  ScriptsActivationActivity.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-06 23:07:10
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the ScriptsActivationActivity object."""

import os
import textwrap

from collections import OrderedDict, namedtuple

import inflect as inflect_mod
import six

from RepositoryBootstrap import Constants
from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl.ActivationActivity import ActivationActivity

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
IGNORE_AS_TOOL_DIR_FILENAME                 = "IgnoreAsTool"

# ----------------------------------------------------------------------
@CommonEnvironmentImports.Interface.staticderived
class ScriptsActivationActivity(ActivationActivity):

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    Name                                    = CommonEnvironmentImports.Interface.DerivedProperty("Scripts")
    DelayExecute                            = CommonEnvironmentImports.Interface.DerivedProperty(False)

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    @CommonEnvironmentImports.Interface.override
    def _CreateCommandsImpl( cls,
                             output_stream,
                             verbose_stream,
                             configuration,
                             repositories,
                             version_specs,
                             generated_dir,
                             no_display_conflicts,
                           ):
        # ----------------------------------------------------------------------
        ExtractorInfo                       = namedtuple( "ExtractorInfo",
                                                          [ "Repository",
                                                            "CreateCommandsFunc",
                                                            "CreateDocumentationFunc",
                                                            "ScriptNameDecoratorFunc",
                                                          ],
                                                        )

        DirGeneratorResult                  = namedtuple( "DirGeneratorResult",
                                                          [ "Dir",
                                                            "Recurse",
                                                          ],
                                                        )

        ScriptInfo                          = namedtuple( "ScriptInfo",
                                                          [ "Repo",
                                                            "Extractor",
                                                            "Filename",
                                                          ],
                                                        )

        WrappedItem                         = namedtuple( "WrappedItem",
                                                          [ "Name",
                                                            "DisplayName",
                                                            "Desc",
                                                            "ScriptInfo",
                                                          ],
                                                        )

        # ----------------------------------------------------------------------

        
        dest_dir = os.path.join(generated_dir, cls.Name)

        verbose_stream.write("Cleaning previous content...")
        with verbose_stream.DoneManager():
            CommonEnvironmentImports.FileSystem.RemoveTree(dest_dir)

        CommonEnvironmentImports.FileSystem.MakeDirs(dest_dir)

        # Scripts can come in a variety of different forms and customization methods
        # may return new ways to traverse a directory. Maintain a list of all potential
        # dir generators to use when parsing script directories.
        dir_generators = [ lambda dir, version_specs: os.path.join(dir, cls.Name),
                         ]

        extractors = OrderedDict()

        verbose_stream.write("Preparing dynamic functionality...")
        with verbose_stream.DoneManager( done_suffixes=[ lambda: "{} found".format(inflect.no("extractor", len(extractors))),
                                                         lambda: "{} found".format(inflect.no("generator", len(dir_generators))),
                                                       ],
                                       ):
            args = { "repositories" : repositories,
                     "version_specs" : version_specs,
                   }

            for repository in repositories:
                result = cls.CallCustomMethod( os.path.join(repository.Root, Constants.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                                               Constants.ACTIVATE_ENVIRONMENT_CUSTOM_SCRIPT_EXTRACTOR_METHOD_NAME,
                                               args,
                                               as_list=False,
                                             )
                if result is None:
                    continue

                # The result can be:
                #
                #       ( ExtractorMap, DirGenerators )
                #       ( ExtractorMap, DirGenerator )
                #       ExtractorMap

                if isinstance(result, tuple):
                    these_extractors, these_generators = result

                    if not isinstance(these_generators, list):
                        these_generators = [ these_generators, ]

                    dir_generators += these_generators
                else:
                    these_extractors = result

                for k, v in six.iteritems(these_extractors):
                    if k in extractors:
                        raise Exception(textwrap.dedent(
                            """\
                            A wrapper for '{ext}' was already defined.

                            New:            {new_name} <{new_id}> [{new_root}]
                            Original:       {original_name} <{original_id}> [{original_root}]
                            """).format( ext=k,
                                         new_name=repository.Name,
                                         new_id=repository.Id,
                                         new_root=repository.Root,
                                         original_name=extractors[k].Repository.Name,
                                         original_id=extractors[k].Repository.Id,
                                         original_root=extractors[k].Repository.Root,
                                       ))

                    # Extract values can be:
                    #
                    #       ( CreateCommands, CreateDocumentation, ScriptNameDecorator )
                    #       ( CreateCommands, CreateDocumentation )
                    #       ( CreateCommands )
                    #       CreateCommands

                    if not isinstance(v, tuple):
                        v = ( v, )

                    extractors[k] = ExtractorInfo( repository,
                                                   v[0],
                                                   v[1] if len(v) > 1 else lambda x: '',
                                                   v[2] if len(v) > 2 else lambda x: x,
                                                 )

        # Get the scrpts
        if extractors:
            script_infos = []

            verbose_stream.write("Searching for content...")
            with verbose_stream.DoneManager( done_suffix=lambda: "{} found".format(inflect.no("script", len(script_infos))),
                                           ):
                
                for repository in repositories:
                    for dir_generator in dir_generators:
                        # Generator values can be:
                        #
                        #       [ (str, recurse), ... ]
                        #       [ str, ... ]
                        #       (str, recurse)
                        #       str

                        results = dir_generator(repository.Root, version_specs)
                        if results is None:
                            continue

                        if not isinstance(results, list):
                            results = [ results, ]

                        for result in results:
                            if isinstance(result, six.string_types):
                                result = DirGeneratorResult(result, True)
                            else:
                                result = DirGeneratorResult(result[0], result[1])

                            if not os.path.isdir(result.Dir):
                                continue

                            if result.Recurse:
                                # ----------------------------------------------------------------------
                                def GenerateFilenames():
                                    for item in CommonEnvironmentImports.FileSystem.WalkFiles( result.Dir,
                                                                                               traverse_exclude_dir_names=[ lambda name: name.lower().endswith("impl"),
                                                                                                                          ],
                                                                                             ):
                                        yield item

                                # ----------------------------------------------------------------------
                            else:
                                # ----------------------------------------------------------------------
                                def GenerateFilenames():
                                    for item in os.listdir(result.Dir):
                                        fullpath = os.path.join(result.Dir, item)

                                        if os.path.isfile(fullpath):
                                            yield fullpath

                                # ----------------------------------------------------------------------

                            for script_filename in GenerateFilenames():
                                ext = os.path.splitext(script_filename)[1]

                                extractor = extractors.get(ext, None)
                                if extractor is None:
                                    continue

                                script_infos.append(ScriptInfo( repository,
                                                                extractor,
                                                                script_filename,
                                                              ))

            if script_infos:
                wrappers = OrderedDict()

                verbose_stream.write("Creating script wrappers...")
                with verbose_stream.DoneManager( done_suffix=lambda: "{} written".format(inflect.no("wrapper", len(wrappers))),
                                               ) as dm:
                    # We have a list of script files and the functions used to extract information
                    # from them. Files were extracted based on repositories ordered from the lowest 
                    # to highest level. However, it is likely that the user will want to use scripts 
                    # from high-level repositories more often than lower-level ones when names collide.
                    # Reverse the order of the higher-level scripts get the standard name while conflicts
                    # in lower-level libraries are renamed.
                    script_infos.reverse()

                    for script_info in script_infos:
                        these_commands = script_info.Extractor.CreateCommandsFunc(script_info.Filename)
                        if these_commands is None:
                            continue

                        # Create an unique name for the wrapper
                        base_name = script_info.Extractor.ScriptNameDecoratorFunc(os.path.splitext(os.path.basename(script_info.Filename))[0])

                        conflicts = []

                        while True:
                            potential_filename = os.path.join(dest_dir, "{}{}{}".format( base_name,
                                                                                         len(conflicts) + 1 if conflicts else '',
                                                                                         CommonEnvironmentImports.CurrentShell.ScriptExtension,
                                                                                       ))

                            if potential_filename in wrappers:
                                conflicts.append(wrappers[potential_filename])
                            else:
                                break

                        base_name = os.path.splitext(os.path.basename(potential_filename))[0]

                        if conflicts and no_display_conflicts:
                            dm.stream.write(textwrap.dedent(
                                """\
                                The wrapper script for '{original_name}' has been renamed '{new_name}' to avoid naming conflicts with:
                                {conflicts}
                                """).format( original_name=script_info.Filename,
                                             new_name=base_name,
                                             conflicts='\n'.join([ "    - {}".format(wrapped_item.ScriptInfo.Filename) for wrapped_item in conflicts ]),
                                           ))

                        with open(potential_filename, 'w') as f:
                            f.write(CommonEnvironmentImports.CurrentShell.GenerateCommands(these_commands))

                        CommonEnvironmentImports.CurrentShell.MakeFileExecutable(potential_filename)

                        assert script_info.Filename.startswith(script_info.Repo.Root), (script_info.Filename, script_info.Repo.Root)
                        display_location = script_info.Filename[len(script_info.Repo.Root):].lstrip(os.path.sep)

                        assert display_location.startswith(Constants.SCRIPTS_SUBDIR), display_location
                        display_location = display_location[len(Constants.SCRIPTS_SUBDIR):].lstrip(os.path.sep)

                        wrappers[potential_filename] = WrappedItem( base_name,
                                                                    display_location,
                                                                    script_info.Extractor.CreateDocumentationFunc(script_info.Filename),
                                                                    script_info,
                                                                  )

                if wrappers:
                    verbose_stream.write("Creating '{}'...".format(Constants.SCRIPT_LIST_NAME))
                    with verbose_stream.DoneManager():
                        these_commands = [ CommonEnvironmentImports.CurrentShell.Commands.EchoOff(),
                                           CommonEnvironmentImports.CurrentShell.Commands.Message("\nAvailable scripts are:\n"),
                                         ]

                        prev_repo = None

                        # Above, we reversed the items so we could order from most-specific to least-specific. Here,
                        # we want to order from least-specific to most specific.
                        wrapper_infos = list(six.itervalues(wrappers))
                        wrapper_infos.reverse()

                        for wrapper_info in wrapper_infos:
                            if wrapper_info.ScriptInfo.Repo != prev_repo:
                                header = "{name:<70} {location:>80}".format( name="{} <{}>".format(wrapper_info.ScriptInfo.Repo.Name, wrapper_info.ScriptInfo.Repo.Id),
                                                                             location=wrapper_info.ScriptInfo.Repo.Root,
                                                                           )

                                these_commands.append(CommonEnvironmentImports.CurrentShell.Commands.Message(textwrap.dedent(
                                    """\
                                    {sep}
                                    {header}
                                    {sep}
                                    """).format( header=header,
                                                 sep='=' * len(header),
                                               )))

                                prev_repo = wrapper_info.ScriptInfo.Repo

                            content = "{0:<68} {1:>78}".format(CommonEnvironmentImports.CurrentShell.CreateScriptName(wrapper_info.Name, filename_only=True), wrapper_info.DisplayName)
                            content += "\n{}\n".format('-' * len(content))

                            if wrapper_info.Desc:
                                content += "{}\n".format(CommonEnvironmentImports.StringHelpers.LeftJustify(wrapper_info.Desc, 2, skip_first_line=False))

                            these_commands.append(CommonEnvironmentImports.CurrentShell.Commands.Message(CommonEnvironmentImports.StringHelpers.LeftJustify(content, 4, skip_first_line=False)))

                        filename = os.path.join(dest_dir, CommonEnvironmentImports.CurrentShell.CreateScriptName(Constants.SCRIPT_LIST_NAME, filename_only=True))

                        with open(filename, 'w') as f:
                            f.write(CommonEnvironmentImports.CurrentShell.GenerateCommands(these_commands))

                        CommonEnvironmentImports.CurrentShell.MakeFileExecutable(filename)

                    # Write output
                    lines = textwrap.dedent(
                                # <Wrong hanging indentation> pylint: disable = C0330
                                """\
                                Shell wrappers have been created for all the recognized files contained within the directory
                                '{script_dir}' across all repositories. For a complete list of these wrappers, run:
                
                                {script_name}
                                """).format( script_dir=cls.Name,
                                             script_name=os.path.basename(filename),
                                           ).rstrip().split('\n')
                
                    max_length = max(*[ len(line) for line in lines ])
                    centered_template = "|  {{:^{}}}  |".format(max_length)
                
                    output_stream.write(textwrap.dedent(
                        """\
                        
                        {line}
                        |  {whitespace}  |
                        {content}
                        |  {whitespace}  |
                        {line}
                
                        """).format( line='-' * (max_length + 6),
                                     whitespace=' ' * max_length,
                                     content='\n'.join([ centered_template.format(line) for line in lines ]),
                                   ))
                        
        return [ CommonEnvironmentImports.CurrentShell.Commands.AugmentPath(dest_dir),
               ]
