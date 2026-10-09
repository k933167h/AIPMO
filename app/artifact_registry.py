"""Provider-independent WBS artifact references."""
import hashlib
import json

KINDS = {"wiki", "file", "message", "test", "defect", "task"}
