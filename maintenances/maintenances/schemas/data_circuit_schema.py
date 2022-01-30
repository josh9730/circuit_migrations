{
    "ticket": {
        "required": False,
        "nullable": True,
        "type": "string",
        "regex": "^(NOC-[0-9]{6,7})|(((COR)|(SYS)|(DEV))-[0-9]{3,5})$",
    },
    "ticket": {
        "required": True,
        "type": "string",
    },
    "device_type": {
        "required": True,
        "type": "string",
        "regex": "^(iosxr)|(junos)$",
    },
    "circuits": {
        "type": "list",
        "required": True,
        "items": [
            {
                "type": "dict",
                "required": True,
                "schema": {
                    "name": {
                        "required": True,
                        "type": "string",
                        "regex": "^(CLR-)[0-9]{4,5}",
                    },
                    "service": {
                        "required": True,
                        "type": "string",
                        "regex": "(ibgp)|(ebgp)|(static)"
                    },
                    "neighbor": { # check if hostname or IPv4
                        "required": True,
                        "type": "string",
                    },
                    "v6_neighbor": { # v6 addressing checks
                        "required": False,
                        "nullable": True,
                        "type": "string",
                    },
                    "port": { # check if valid port
                        "required": True,
                        "type": "string",
                    },
                },
            },
        ],
    },
}
