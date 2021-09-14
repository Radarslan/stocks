:: format app
isort --force-single-line-imports app
black app
autoflake --recursive --remove-all-unused-imports --remove-unused-variables --in-place app --exclude=__init__.py