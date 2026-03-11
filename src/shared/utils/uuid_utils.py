"""
UUID Utilities

Provides UUID utilities for Python < 3.11 compatibility.
"""
from uuid import UUID

# NIL_UUID constant for Python < 3.11 compatibility
# In Python 3.11+, this is available as uuid.NIL_UUID
NIL_UUID = UUID('00000000-0000-0000-0000-000000000000')