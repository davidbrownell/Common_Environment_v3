# ---------------------------------------------------------------------------
# |
# |  WARNING:
# |  This file was generated; any local changes will be overwritten during 
# |  future invocations of the generator!
# |
# ---------------------------------------------------------------------------


# <Method could be a function> pylint: disable = R0201
# <Too few public methods> pylint: disable = R0903
# <Too many public methods> pylint: disable = R0904
# <Too many brances> pylint: disable = R0912
# <Too many statements> pylint: disable = R0915
# <Invalid function name> pylint: disable = C0103
# <Too many lines in module> pylint: disable = C0302
# <Unused argument> pylint: disable = W0613

import json
import textwrap

from collections import OrderedDict

import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.TypeInfo import Arity, ValidationException
from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
from CommonEnvironment.TypeInfo.ClassTypeInfo import ClassTypeInfo
from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.JsonLikeSerialization import JsonLikeSerialization

# ----------------------------------------------------------------------
class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__

# ----------------------------------------------------------------------
# |  
# |  Utility Methods
# |  
# ----------------------------------------------------------------------
def FromJson(root):
    result = Object()

    this_result = Commit_FromJson(root, is_root=True)
    if this_result != None:
        setattr(result, "Commit", this_result)
    
    this_result = Push_FromJson(root, is_root=True)
    if this_result != None:
        setattr(result, "Push", this_result)
    
    this_result = Pushed_FromJson(root, is_root=True)
    if this_result != None:
        setattr(result, "Pushed", this_result)

    return result

# ----------------------------------------------------------------------
# |     
# |  FromJson
# |  
# ----------------------------------------------------------------------
def Commit_FromJson(item, always_include_optional=False, process_additional_data=False, is_root=False):
    # ----------------------------------------------------------------------
    def LoadImpl():
        if not isinstance(item, list):
            if is_root:
                if isinstance(item, six.string_types):
                    return json.loads(item)
    
                if hasattr(item, "read"):
                    return json.load(item)
    
            if isinstance(item, dict):
                if "Commit" in item:
                    return item["Commit"]
            elif hasattr(item, "Commit"):
                return getattr(item, "Commit")
    
            if is_root:
                return None
    
        return item
    
    # ----------------------------------------------------------------------
    
    item = LoadImpl()

    Commit_TypeInfo.ValidateArity(item)

    if item == None:
        return None

    parser = _FromParser()

    result = parser.Commit_ItemFromJson(item, always_include_optional, process_additional_data)

    return result                            

# ----------------------------------------------------------------------
def Push_FromJson(item, always_include_optional=False, process_additional_data=False, is_root=False):
    # ----------------------------------------------------------------------
    def LoadImpl():
        if not isinstance(item, list):
            if is_root:
                if isinstance(item, six.string_types):
                    return json.loads(item)
    
                if hasattr(item, "read"):
                    return json.load(item)
    
            if isinstance(item, dict):
                if "Push" in item:
                    return item["Push"]
            elif hasattr(item, "Push"):
                return getattr(item, "Push")
    
            if is_root:
                return None
    
        return item
    
    # ----------------------------------------------------------------------
    
    item = LoadImpl()

    Push_TypeInfo.ValidateArity(item)

    if item == None:
        return None

    parser = _FromParser()

    result = parser.Push_ItemFromJson(item, always_include_optional, process_additional_data)

    return result                            

# ----------------------------------------------------------------------
def Pushed_FromJson(item, always_include_optional=False, process_additional_data=False, is_root=False):
    # ----------------------------------------------------------------------
    def LoadImpl():
        if not isinstance(item, list):
            if is_root:
                if isinstance(item, six.string_types):
                    return json.loads(item)
    
                if hasattr(item, "read"):
                    return json.load(item)
    
            if isinstance(item, dict):
                if "Pushed" in item:
                    return item["Pushed"]
            elif hasattr(item, "Pushed"):
                return getattr(item, "Pushed")
    
            if is_root:
                return None
    
        return item
    
    # ----------------------------------------------------------------------
    
    item = LoadImpl()

    Pushed_TypeInfo.ValidateArity(item)

    if item == None:
        return None

    parser = _FromParser()

    result = parser.Pushed_ItemFromJson(item, always_include_optional, process_additional_data)

    return result                            

# ----------------------------------------------------------------------
# |  
# |  TypeInfo
# |  
# ----------------------------------------------------------------------
ChangeInfo_TypeInfo                                                         = AnyOfTypeInfo(arity=Arity(min=1, max_or_none=1), type_info_list=[ DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "id" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1), "author" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1), "date" : DateTimeTypeInfo(arity=Arity(min=1, max_or_none=1)), "description" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=0), "branch" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1) }, require_exact_match=None), ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "id" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1), "author" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1), "date" : DateTimeTypeInfo(arity=Arity(min=1, max_or_none=1)), "description" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=0), "branch" : StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1) }, require_exact_match=None) ])
ChangeInfo_id_TypeInfo                                                      = StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1)
ChangeInfo_author_TypeInfo                                                  = StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1)
ChangeInfo_date_TypeInfo                                                    = DateTimeTypeInfo(arity=Arity(min=1, max_or_none=1))
ChangeInfo_description_TypeInfo                                             = StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=0)
ChangeInfo_branch_TypeInfo                                                  = StringTypeInfo(arity=Arity(min=1, max_or_none=1), min_length=1)
Commit_TypeInfo                                                             = AnyOfTypeInfo(arity=Arity(min=1, max_or_none=1), type_info_list=[ DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "modified" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=True, match_any=False), "added" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=True, match_any=False), "removed" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False) }, require_exact_match=None), ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "modified" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=True, match_any=False), "added" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=True, match_any=False), "removed" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False) }, require_exact_match=None) ])
Commit_modified_TypeInfo                                                    = FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=True, match_any=False)
Commit_added_TypeInfo                                                       = FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=True, match_any=False)
Commit_removed_TypeInfo                                                     = FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False)
Push_TypeInfo                                                               = AnyOfTypeInfo(arity=Arity(min=1, max_or_none=1), type_info_list=[ DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "url" : StringTypeInfo(arity=Arity(min=0, max_or_none=1), min_length=1) }, require_exact_match=None), ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "url" : StringTypeInfo(arity=Arity(min=0, max_or_none=1), min_length=1) }, require_exact_match=None) ])
Push_url_TypeInfo                                                           = StringTypeInfo(arity=Arity(min=0, max_or_none=1), min_length=1)
Pushed_TypeInfo                                                             = AnyOfTypeInfo(arity=Arity(min=1, max_or_none=1), type_info_list=[ DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "changes" : AnyOfTypeInfo(arity=Arity(min=1, max_or_none=None), type_info_list=[ DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "modified" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "added" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "removed" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False) }, require_exact_match=None), ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "modified" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "added" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "removed" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False) }, require_exact_match=None) ]) }, require_exact_match=None), ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "changes" : AnyOfTypeInfo(arity=Arity(min=1, max_or_none=None), type_info_list=[ DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "modified" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "added" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "removed" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False) }, require_exact_match=None), ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "modified" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "added" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "removed" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False) }, require_exact_match=None) ]) }, require_exact_match=None) ])
Pushed_changes_TypeInfo                                                     = AnyOfTypeInfo(arity=Arity(min=1, max_or_none=None), type_info_list=[ DictTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "modified" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "added" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "removed" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False) }, require_exact_match=None), ClassTypeInfo(arity=Arity(min=1, max_or_none=1), items={ "modified" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "added" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False), "removed" : FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False) }, require_exact_match=None) ])
Pushed_changes_modified_TypeInfo                                            = FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False)
Pushed_changes_added_TypeInfo                                               = FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False)
Pushed_changes_removed_TypeInfo                                             = FilenameTypeInfo(arity=Arity(min=0, max_or_none=None), ensure_exists=False, match_any=False)

# ----------------------------------------------------------------------
class Object(object):           pass
class DoesNotExist(object):     pass

# ----------------------------------------------------------------------
def _ValidateUniqueKeys(unique_key_attribute_name, items):
    unique_keys = set()

    for item in items:
        if isinstance(item, dict):
            unique_key = item.get(unique_key_attribute_name)
        else:
            unique_key = getattr(item, unique_key_attribute_name)

        if unique_key in unique_keys:
            raise Exception("The unique key '{}' was not unique: {}".format( unique_key_attribute_name,
                                                                             unique_key,
                                                                           ))

        unique_keys.add(unique_key)

# ----------------------------------------------------------------------
def _ProcessException(frame_desc):
    exception = sys.exc_info()[1]

    if not hasattr(exception, "stack"):
        setattr(exception, "stack", [])

    exception.stack.insert(0, frame_desc)
    raise

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# |
# |  Helpers
# |
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  _FromParser
# |  
# ----------------------------------------------------------------------
class _FromParser(object):

    # ----------------------------------------------------------------------
    def ChangeInfo_id_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(ChangeInfo_id_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def ChangeInfo_author_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(ChangeInfo_author_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def ChangeInfo_date_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(ChangeInfo_date_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def ChangeInfo_description_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(ChangeInfo_description_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def ChangeInfo_branch_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(ChangeInfo_branch_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def ChangeInfo_ItemFromJson(self, item, always_include_optional, process_additional_data):
        item_attributes = set([ name for name in six.iterkeys(item) if name[0] != '_' ])
    
        result = Object()
        
        # id
        try:
            this_item = getattr(item, "get", lambda a, b: b)("id", DoesNotExist)
            
            ChangeInfo_id_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "id", self.ChangeInfo_id_ItemFromJson(this_item))
            item_attributes.remove("id")
        
        except:
            _ProcessException("id")
        
        # author
        try:
            this_item = getattr(item, "get", lambda a, b: b)("author", DoesNotExist)
            
            ChangeInfo_author_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "author", self.ChangeInfo_author_ItemFromJson(this_item))
            item_attributes.remove("author")
        
        except:
            _ProcessException("author")
        
        # date
        try:
            this_item = getattr(item, "get", lambda a, b: b)("date", DoesNotExist)
            
            ChangeInfo_date_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "date", self.ChangeInfo_date_ItemFromJson(this_item))
            item_attributes.remove("date")
        
        except:
            _ProcessException("date")
        
        # description
        try:
            this_item = getattr(item, "get", lambda a, b: b)("description", DoesNotExist)
            
            ChangeInfo_description_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "description", self.ChangeInfo_description_ItemFromJson(this_item))
            item_attributes.remove("description")
        
        except:
            _ProcessException("description")
        
        # branch
        try:
            this_item = getattr(item, "get", lambda a, b: b)("branch", DoesNotExist)
            
            ChangeInfo_branch_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "branch", self.ChangeInfo_branch_ItemFromJson(this_item))
            item_attributes.remove("branch")
        
        except:
            _ProcessException("branch")
        
        # Additional data
        if process_additional_data:
            self._ProcessAdditionalData(item, result, exclude_names={ "id", "author", "date", "description", "branch" })
        elif item_attributes:
            raise ValidationException("The item contains extraneous data: {}".format(', '.join([ "'{}'".format(item_attribute) for item_attribute in item_attributes ])))
    
        ChangeInfo_TypeInfo.ValidateItem(result, recurse=False, require_exact_match=not process_additional_data, exclude_names=[ "id", "author", "date", "description", "branch" ])
        return result
    
    # ----------------------------------------------------------------------
    def Commit_modified_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(Commit_modified_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def Commit_added_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(Commit_added_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def Commit_removed_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(Commit_removed_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def Commit_ItemFromJson(self, item, always_include_optional, process_additional_data):
        item_attributes = set([ name for name in six.iterkeys(item) if name[0] != '_' ])
    
        result = Object()
        
        # modified
        try:
            these_items = getattr(item, "get", lambda a, b: b)("modified", DoesNotExist)
            if these_items == DoesNotExist:
                these_items = []
            
            Commit_modified_TypeInfo.ValidateArity(these_items)
            
            these_results = []
            
            for this_index, this_item in enumerate(these_items):
                try:
                    these_results.append(self.Commit_modified_ItemFromJson(this_item))
                except:
                    _ProcessException("Index {}".format(this_index))
            
            setattr(result, "modified", these_results)
            item_attributes.discard("modified")
        
        except:
            _ProcessException("modified")
        
        # added
        try:
            these_items = getattr(item, "get", lambda a, b: b)("added", DoesNotExist)
            if these_items == DoesNotExist:
                these_items = []
            
            Commit_added_TypeInfo.ValidateArity(these_items)
            
            these_results = []
            
            for this_index, this_item in enumerate(these_items):
                try:
                    these_results.append(self.Commit_added_ItemFromJson(this_item))
                except:
                    _ProcessException("Index {}".format(this_index))
            
            setattr(result, "added", these_results)
            item_attributes.discard("added")
        
        except:
            _ProcessException("added")
        
        # removed
        try:
            these_items = getattr(item, "get", lambda a, b: b)("removed", DoesNotExist)
            if these_items == DoesNotExist:
                these_items = []
            
            Commit_removed_TypeInfo.ValidateArity(these_items)
            
            these_results = []
            
            for this_index, this_item in enumerate(these_items):
                try:
                    these_results.append(self.Commit_removed_ItemFromJson(this_item))
                except:
                    _ProcessException("Index {}".format(this_index))
            
            setattr(result, "removed", these_results)
            item_attributes.discard("removed")
        
        except:
            _ProcessException("removed")
        
        # id
        try:
            this_item = getattr(item, "get", lambda a, b: b)("id", DoesNotExist)
            
            ChangeInfo_id_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "id", self.ChangeInfo_id_ItemFromJson(this_item))
            item_attributes.remove("id")
        
        except:
            _ProcessException("id")
        
        # author
        try:
            this_item = getattr(item, "get", lambda a, b: b)("author", DoesNotExist)
            
            ChangeInfo_author_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "author", self.ChangeInfo_author_ItemFromJson(this_item))
            item_attributes.remove("author")
        
        except:
            _ProcessException("author")
        
        # date
        try:
            this_item = getattr(item, "get", lambda a, b: b)("date", DoesNotExist)
            
            ChangeInfo_date_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "date", self.ChangeInfo_date_ItemFromJson(this_item))
            item_attributes.remove("date")
        
        except:
            _ProcessException("date")
        
        # description
        try:
            this_item = getattr(item, "get", lambda a, b: b)("description", DoesNotExist)
            
            ChangeInfo_description_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "description", self.ChangeInfo_description_ItemFromJson(this_item))
            item_attributes.remove("description")
        
        except:
            _ProcessException("description")
        
        # branch
        try:
            this_item = getattr(item, "get", lambda a, b: b)("branch", DoesNotExist)
            
            ChangeInfo_branch_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "branch", self.ChangeInfo_branch_ItemFromJson(this_item))
            item_attributes.remove("branch")
        
        except:
            _ProcessException("branch")
        
        # Additional data
        if process_additional_data:
            self._ProcessAdditionalData(item, result, exclude_names={ "modified", "added", "removed", "id", "author", "date", "description", "branch" })
        elif item_attributes:
            raise ValidationException("The item contains extraneous data: {}".format(', '.join([ "'{}'".format(item_attribute) for item_attribute in item_attributes ])))
    
        Commit_TypeInfo.ValidateItem(result, recurse=False, require_exact_match=not process_additional_data, exclude_names=[ "modified", "added", "removed", "id", "author", "date", "description", "branch" ])
        return result
    
    # ----------------------------------------------------------------------
    def Push_url_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(Push_url_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def Push_ItemFromJson(self, item, always_include_optional, process_additional_data):
        item_attributes = set([ name for name in six.iterkeys(item) if name[0] != '_' ])
    
        result = Object()
        
        # url
        try:
            self._ApplyOptionalChild(item, "url", result, self.Push_url_ItemFromJson, always_include_optional)
            item_attributes.discard("url")
        
        except:
            _ProcessException("url")
        
        # Additional data
        if process_additional_data:
            self._ProcessAdditionalData(item, result, exclude_names={ "url" })
        elif item_attributes:
            raise ValidationException("The item contains extraneous data: {}".format(', '.join([ "'{}'".format(item_attribute) for item_attribute in item_attributes ])))
    
        Push_TypeInfo.ValidateItem(result, recurse=False, require_exact_match=not process_additional_data, exclude_names=[ "url" ])
        return result
    
    # ----------------------------------------------------------------------
    def Pushed_changes_modified_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(Pushed_changes_modified_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def Pushed_changes_added_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(Pushed_changes_added_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def Pushed_changes_removed_ItemFromJson(self, item):
        return JsonLikeSerialization.DeserializeItem(Pushed_changes_removed_TypeInfo, item)
    
    # ----------------------------------------------------------------------
    def Pushed_changes_ItemFromJson(self, item, always_include_optional, process_additional_data):
        item_attributes = set([ name for name in six.iterkeys(item) if name[0] != '_' ])
    
        result = Object()
        
        # modified
        try:
            these_items = getattr(item, "get", lambda a, b: b)("modified", DoesNotExist)
            if these_items == DoesNotExist:
                these_items = []
            
            Pushed_changes_modified_TypeInfo.ValidateArity(these_items)
            
            these_results = []
            
            for this_index, this_item in enumerate(these_items):
                try:
                    these_results.append(self.Pushed_changes_modified_ItemFromJson(this_item))
                except:
                    _ProcessException("Index {}".format(this_index))
            
            setattr(result, "modified", these_results)
            item_attributes.discard("modified")
        
        except:
            _ProcessException("modified")
        
        # added
        try:
            these_items = getattr(item, "get", lambda a, b: b)("added", DoesNotExist)
            if these_items == DoesNotExist:
                these_items = []
            
            Pushed_changes_added_TypeInfo.ValidateArity(these_items)
            
            these_results = []
            
            for this_index, this_item in enumerate(these_items):
                try:
                    these_results.append(self.Pushed_changes_added_ItemFromJson(this_item))
                except:
                    _ProcessException("Index {}".format(this_index))
            
            setattr(result, "added", these_results)
            item_attributes.discard("added")
        
        except:
            _ProcessException("added")
        
        # removed
        try:
            these_items = getattr(item, "get", lambda a, b: b)("removed", DoesNotExist)
            if these_items == DoesNotExist:
                these_items = []
            
            Pushed_changes_removed_TypeInfo.ValidateArity(these_items)
            
            these_results = []
            
            for this_index, this_item in enumerate(these_items):
                try:
                    these_results.append(self.Pushed_changes_removed_ItemFromJson(this_item))
                except:
                    _ProcessException("Index {}".format(this_index))
            
            setattr(result, "removed", these_results)
            item_attributes.discard("removed")
        
        except:
            _ProcessException("removed")
        
        # id
        try:
            this_item = getattr(item, "get", lambda a, b: b)("id", DoesNotExist)
            
            ChangeInfo_id_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "id", self.ChangeInfo_id_ItemFromJson(this_item))
            item_attributes.remove("id")
        
        except:
            _ProcessException("id")
        
        # author
        try:
            this_item = getattr(item, "get", lambda a, b: b)("author", DoesNotExist)
            
            ChangeInfo_author_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "author", self.ChangeInfo_author_ItemFromJson(this_item))
            item_attributes.remove("author")
        
        except:
            _ProcessException("author")
        
        # date
        try:
            this_item = getattr(item, "get", lambda a, b: b)("date", DoesNotExist)
            
            ChangeInfo_date_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "date", self.ChangeInfo_date_ItemFromJson(this_item))
            item_attributes.remove("date")
        
        except:
            _ProcessException("date")
        
        # description
        try:
            this_item = getattr(item, "get", lambda a, b: b)("description", DoesNotExist)
            
            ChangeInfo_description_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "description", self.ChangeInfo_description_ItemFromJson(this_item))
            item_attributes.remove("description")
        
        except:
            _ProcessException("description")
        
        # branch
        try:
            this_item = getattr(item, "get", lambda a, b: b)("branch", DoesNotExist)
            
            ChangeInfo_branch_TypeInfo.ValidateArityCount(1 if this_item != DoesNotExist else 0)
            setattr(result, "branch", self.ChangeInfo_branch_ItemFromJson(this_item))
            item_attributes.remove("branch")
        
        except:
            _ProcessException("branch")
        
        # Additional data
        if process_additional_data:
            self._ProcessAdditionalData(item, result, exclude_names={ "modified", "added", "removed", "id", "author", "date", "description", "branch" })
        elif item_attributes:
            raise ValidationException("The item contains extraneous data: {}".format(', '.join([ "'{}'".format(item_attribute) for item_attribute in item_attributes ])))
    
        Pushed_changes_TypeInfo.ValidateItem(result, recurse=False, require_exact_match=not process_additional_data, exclude_names=[ "modified", "added", "removed", "id", "author", "date", "description", "branch" ])
        return result
    
    # ----------------------------------------------------------------------
    def Pushed_ItemFromJson(self, item, always_include_optional, process_additional_data):
        item_attributes = set([ name for name in six.iterkeys(item) if name[0] != '_' ])
    
        result = Object()
        
        # changes
        try:
            these_items = getattr(item, "get", lambda a, b: b)("changes", DoesNotExist)
            if these_items == DoesNotExist:
                these_items = []
            
            Pushed_changes_TypeInfo.ValidateArity(these_items)
            
            these_results = []
            
            for this_index, this_item in enumerate(these_items):
                try:
                    these_results.append(self.Pushed_changes_ItemFromJson(this_item, always_include_optional, process_additional_data))
                except:
                    _ProcessException("Index {}".format(this_index))
            
            setattr(result, "changes", these_results)
            item_attributes.remove("changes")
        
        except:
            _ProcessException("changes")
        
        # Additional data
        if process_additional_data:
            self._ProcessAdditionalData(item, result, exclude_names={ "changes" })
        elif item_attributes:
            raise ValidationException("The item contains extraneous data: {}".format(', '.join([ "'{}'".format(item_attribute) for item_attribute in item_attributes ])))
    
        Pushed_TypeInfo.ValidateItem(result, recurse=False, require_exact_match=not process_additional_data, exclude_names=[ "changes" ])
        return result
    
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _ProcessAdditionalData(cls, source, dest, exclude_names=None):
        exclude_names = exclude_names or set()
    
        for k, v in six.iteritems(source):
            if k[0] != '_' and k not in exclude_names:
                if isinstance(v, dict):
                    child = Object()
        
                    cls._ProcessAdditionalData(v, child)
                    setattr(dest, k, child)
                else:
                    setattr(dest, k, v)
    
    # ----------------------------------------------------------------------
    @classmethod
    def _ApplyOptionalChild(cls, obj, attribute_name, dest, func, always_include_optional):
        this_item = getattr(obj, "get", lambda a, b: b)(attribute_name, DoesNotExist)
        if this_item != DoesNotExist:
            setattr(dest, attribute_name, func(this_item))
            return
    
        if always_include_optional:
            setattr(dest, attribute_name, None)
    
