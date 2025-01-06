import json
from typing import Any, Dict, Optional

from kstreams import types


class JsonSerializer:
    async def serialize(
        self,
        payload: Any,
        headers: Optional[types.Headers] = None,
        serializer_kwargs: Optional[Dict] = None,
    ) -> bytes:
        """
        Serialize paylod to json
        """
        value = json.dumps(payload)
        return value.encode()
