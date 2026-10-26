"""Bounded tensor reads for Windows machines where mmap storage slicing crashes.

Reads the standard safetensors header and one tensor at a time. No pickle,
quantization, weight changes, or inference on CPU is involved.
"""
import json,struct
import torch

DTYPES={'F64':torch.float64,'F32':torch.float32,'F16':torch.float16,'BF16':torch.bfloat16,'I64':torch.int64,'I32':torch.int32,'I16':torch.int16,'I8':torch.int8,'U8':torch.uint8,'BOOL':torch.bool}

class Slice:
    def __init__(self,reader,key): self.reader=reader;self.key=key
    def get_shape(self):return self.reader.header[self.key]['shape']
    def get_dtype(self):return self.reader.header[self.key]['dtype']
    def __getitem__(self,index):return self.reader.get_tensor(self.key)[index]

class SafeReader:
    def __init__(self,filename,framework='pt',device='cpu'):
        if framework!='pt':raise ValueError('Only PyTorch is supported')
        self.filename=filename
        with open(filename,'rb') as f:
            length=struct.unpack('<Q',f.read(8))[0]
            if length>100_000_000:raise ValueError('Invalid safetensors header')
            self.header=json.loads(f.read(length));self.offset=8+length
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def keys(self):return [key for key in self.header if key!='__metadata__']
    def metadata(self):return self.header.get('__metadata__')
    def get_slice(self,key):return Slice(self,key)
    def get_tensor(self,key):
        item=self.header[key];start,end=item['data_offsets'];size=end-start
        with open(self.filename,'rb') as f:
            f.seek(self.offset+start);data=bytearray(f.read(size))
        if len(data)!=size:raise ValueError('Incomplete safetensors tensor')
        return torch.frombuffer(data,dtype=DTYPES[item['dtype']]).reshape(item['shape'])

def enable_windows_safe_reader():
    import transformers.modeling_utils
    transformers.modeling_utils.safe_open=SafeReader
