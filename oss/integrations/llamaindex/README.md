# LlamaIndex Integration

LlamaIndex adapter for Continuum decision operations.

## Install

```bash
pip install continuum-sdk continuum-llamaindex
```

## Usage

```python
from continuum_llamaindex import ContinuumToolSpec

tools = ContinuumToolSpec(storage_dir=".continuum").spec_functions
```
