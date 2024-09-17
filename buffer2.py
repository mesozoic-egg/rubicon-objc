import os
import sys
from ctypes import *
from typing import *
from rubicon.objc import NSUInteger
from rubicon.objc import types
import rubicon.objc as ru
from rubicon.objc.runtime import libobjc
from rubicon.objc.api import py_from_ns
def main():

    _MTLSizeEncoding = b'{?=QQQ}'
    @types.with_preferred_encoding(_MTLSizeEncoding)
    class MTLSize(Structure):
        _fields_ = [
            ("width",  NSUInteger),
            ("height", NSUInteger),
            ("depth",  NSUInteger),
        ]
    cg = ru.runtime.load_library("CoreGraphics")
    metal = ru.runtime.load_library('Metal')
    metal.MTLCreateSystemDefaultDevice.restype = ru.runtime.objc_id
    
    device = metal.MTLCreateSystemDefaultDevice()
    device = ru.ObjCInstance(device)
    MTLCompileOptionsClass   = libobjc.objc_getClass(b"MTLCompileOptions")
    MTLCompileOptionsClass = ru.ObjCClass(MTLCompileOptionsClass)
    MTLCompileOptions = MTLCompileOptionsClass.new()
    
    library = device.newLibraryWithSource_options_error_("""
#include <metal_stdlib>
using namespace metal;

kernel void add(const device float2 *in [[ buffer(0) ]],
                device float  *out [[ buffer(1) ]],
                uint id [[ thread_position_in_grid ]]) {
    out[id] = in[id].x + in[id].y;
}
""", MTLCompileOptions, None)
    kernelFunction = library.newFunctionWithName_("add")
    commandQueue = device.newCommandQueue()
    commandBuffer = commandQueue.commandBuffer()
    encoder = commandBuffer.computeCommandEncoder()

    computePipelineState = device.newComputePipelineStateWithFunction_error_(
        kernelFunction,
        None
    )
    encoder.setComputePipelineState_(computePipelineState)

    _input = [1,2]
    _input_ptr = (c_float * len(_input))(*_input)
    buf = device.newBufferWithBytesNoCopy_length_options_deallocator_(
        _input_ptr,
        2 * sizeof(c_float),
        0,
        None
    )
    buf_instance = ru.ObjCInstance(buf)
    input_contents = buf_instance.contents
    print((c_float * 2).from_address(input_contents.value)[:])
    
    encoder.setBuffer_offset_atIndex_(
        buf,
        0,
        0
    )
    outputBuffer = device.newBufferWithLength_options_(
        1 * sizeof(c_float),
        0
    )
    encoder.setBuffer_offset_atIndex_(
        outputBuffer,
        0,
        1
    )
    encoder.dispatchThreadgroups_threadsPerThreadgroup_(
        (1,1,1),
        (1,1,1)
    )
    encoder.endEncoding()
    commandBuffer.commit()
    commandBuffer.waitUntilCompleted()
    
    # print(outputBuffer)
    # print(f"{outputBuffer.contents}")
    print((c_float * 1).from_address(outputBuffer.contents.value)[:])

    	      
if __name__ == '__main__':
    main()