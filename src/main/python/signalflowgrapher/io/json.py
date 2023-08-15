from signalflow_algorithms.common.json_dict import JSONDict
from typing import Dict, Any
import json
import logging
import jsonschema
from jsonschema.validators import validate
from signalflowgrapher.io.file import write_file, read_file
logger = logging.getLogger(__name__)


class JSONExport(object):
    """
    JSONExport allows to write json to file.
    """

    def __init__(self):
        super().__init__()

    def write_as_json(self, data: JSONDict, path: str):
        """
        Write data to file at path.
        """
        logger.info("Write json to file %s", path)
        json_data = json.dumps(data.to_dict(), indent=4)
        write_file(path, json_data)


class JSONImport(object):
    """
    JSONImport allows to read json from file.
    """

    def __init__(self):
        super().__init__()

    def read_from_json(self, path: str) -> Dict:
        """
        Read json data from file at path.
        """
        try:
            content = read_file(path)
            data = json.loads(content)
        except ValueError as e:
            logger.error("File %s contains invalid json: %s",
                         path,
                         str(e))
            raise

        # Validate schema of json, raises Exception if invalid
        validator = JSONValidator()
        validator.validate_json(data)
        return data


class JSONValidator(object):
    """
    Validator for validation of json schema of graph.
    """

    def __init__(self):
        super().__init__()
        self.__graph_schema = {
            "type": "object",
            "properties": {
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string"
                            },
                            "label_dx": {
                                "type": "integer"
                            },
                            "label_dy": {
                                "type": "integer"
                            },
                            "name": {
                                "type": "string"
                            },
                            "x": {
                                "type": "integer"
                            },
                            "y": {
                                "type": "integer"
                            }
                        },
                        "required": [
                            "id",
                            "label_dx",
                            "label_dy",
                            "name",
                            "x",
                            "y"
                        ]
                    }
                },
                "branches": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string"
                            },
                            "weight": {
                                "type": "string"
                            },
                            "start": {
                                "type": "string"
                            },
                            "end": {
                                "type": "string"
                            },
                            "label_dx": {
                                "type": "number"
                            },
                            "label_dy": {
                                "type": "number"
                            },
                            "spline1_x": {
                                "type": "number"
                            },
                            "spline1_y": {
                                "type": "number"
                            },
                            "spline2_x": {
                                "type": "number"
                            },
                            "spline2_y": {
                                "type": "number"
                            }
                        },
                        "required": [
                            "id",
                            "weight",
                            "start",
                            "end",
                            "label_dx",
                            "label_dy",
                            "spline1_x",
                            "spline1_y",
                            "spline2_x",
                            "spline2_y"
                        ]
                    }
                }
            },
            "required": [
                "nodes",
                "branches"
            ]
        }

    def validate_json(self, data: Any):
        """
        Validate data with graph schema. Raises validation error
        if validation fails.
        """
        try:
            validate(instance=data, schema=self.__graph_schema)
        except jsonschema.exceptions.ValidationError as e:
            logger.error("Loaded invalid json file %s", str(e))
            raise jsonschema.exceptions.ValidationError()
