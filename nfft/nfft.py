# Copyright (c) 2016, Imperial College London
# Copyright (c) 2016, Ghislain Antony Vaillant
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the BSD license. See the accompanying LICENSE file
# or read the terms at https://opensource.org/licenses/BSD-3-Clause.

from __future__ import division
from ._ffi import ffi, lib
from contextlib import contextmanager
from enum import IntEnum
from numpy import ascontiguousarray, empty

__all__ = ('nfft', 'nffth')


@contextmanager
def make_plan(f_hat, f, x, m=12):
    from functools import reduce
    from operator import or_

    class Flag(IntEnum):
        PRE_PHI_HUT      = 2**0
        FG_PSI           = 2**1
        PRE_LIN_PSI      = 2**2
        PRE_FG_PSI       = 2**3
        PRE_PSI          = 2**4
        PRE_FULL_PSI     = 2**5
        FFT_OUT_OF_PLACE = 2**9
        FFTW_INIT        = 2**10

    def to_native_const_int(iterable):
        return ffi.new("const int []", iterable)

    def to_native_cdouble(buffer):
        return ffi.cast("fftw_complex *", ffi.from_buffer(buffer))

    def to_native_double(buffer):
        return ffi.cast("double *", ffi.from_buffer(buffer))

    flags = (Flag.PRE_PHI_HUT, Flag.PRE_PSI, Flag.FFT_OUT_OF_PLACE,
             Flag.FFTW_INIT)

    p = ffi.new("nfft_plan *")
    lib.nfft_init_guru(p, f_hat.ndim, to_native_const_int(f_hat.shape), f.size,
                       to_native_const_int([2 * d for d in f_hat.shape]), m,
                       reduce(or_, flags, 0), 1)

    p.f_hat = to_native_cdouble(memoryview(f_hat))
    p.f = to_native_cdouble(memoryview(f))
    p.x = to_native_double(memoryview(x))

    yield p

    lib.nfft_finalize(p)


def nfft(f_hat, x, *args, **kwargs):
    """
    Compute the forward non-uniform Fourier transform.
    """
    f_hat = ascontiguousarray(f_hat, dtype='cdouble')
    x = ascontiguousarray(x, dtype='double')
    f = empty(x.size//f_hat.ndim, dtype='cdouble')

    with make_plan(f_hat, f, x, *args, **kwargs) as p:
        lib.nfft_precompute_one_psi(p)
        lib.nfft_trafo(p)

    return f


def nffth(f, x, N, *args, **kwargs):
    """
    Compute the adjoint non-uniform Fourier transform.
    """
    f = ascontiguousarray(f, dtype='cdouble')
    x = ascontiguousarray(x, dtype='double')
    f_hat = empty(N, dtype='cdouble')

    with make_plan(f_hat, f, x, *args, **kwargs) as p:
        lib.nfft_precompute_one_psi(p)
        lib.nfft_adjoint(p)

    return f_hat

