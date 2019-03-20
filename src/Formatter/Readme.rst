Formats Python code using Black (https://github.com/ambv/black) plus enhancements:

- Aligns assignments within a block
- Aligns trailing comments within a block
- Ensures that all line-delimied parameters and arguments include a trailing comma
- Reverts splits for empty parens
- Fine-grained control over line splitting for:
    * parameters
    * arguments
    * list items
    * dict items
    * tuple items
- Fixes inconsitencies with textwrap.dedent and multiline strings
