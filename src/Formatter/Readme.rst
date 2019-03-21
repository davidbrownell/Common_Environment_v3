Formats Python code using Black (https://github.com/ambv/black) plus enhancements:

- Aligns assignments within a block
- Aligns trailing comments within a block
- Ensures that all line-delimited parameters and arguments include a trailing comma
- Ensures that all logical clauses are line-delimited in any are
- Reverts splits for empty parens
- Fine-grained control over line splitting for:
    * parameters
    * arguments
    * list items
    * dict items
    * tuple items
- Fixes inconsistencies with textwrap.dedent and multiline strings
