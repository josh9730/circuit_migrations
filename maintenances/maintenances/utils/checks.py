from cerberus import Validator


def data_checks(yaml_file):
    """Check user-supplied yaml file"""

    schema = eval(open("schemas/data_circuit_schema.py", "r").read())
    v = Validator(schema, allow_unknown=True)
    v.validate(yaml_file)
    if v.errors:
        print(v.errors)
        exit(1)