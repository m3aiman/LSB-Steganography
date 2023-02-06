from math import ceil

import numpy as np

byte_depth_to_dtype = {1: np.uint8, 2: np.uint16, 4: np.uint32, 8: np.uint64}


def roundup(x, base=1):
    return int(ceil(x / base)) * base


def lsb_interleave_bytes(carrier, payload, num_lsb, truncate=False, byte_depth=1):
    """
    Interleave the bytes of payload into the num_lsb LSBs of carrier.
    :carrier: carrier bytes
    :payload: payload bytes
    :num_lsb: number of least significant bits to use
    :truncate: if True, will only return the interleaved part
    :byte_depth: byte depth of carrier values
    :return: The interleaved bytes
    """

    plen = len(payload)
    payload_bits = np.zeros(shape=(plen, 8), dtype=np.uint8)
    payload_bits[:plen, :] = np.unpackbits(
        np.frombuffer(payload, dtype=np.uint8, count=plen)
    ).reshape(plen, 8)

    bit_height = roundup(plen * 8 / num_lsb)
    payload_bits.resize(bit_height * num_lsb)

    carrier_dtype = byte_depth_to_dtype[byte_depth]
    carrier_bits = np.unpackbits(
        np.frombuffer(carrier, dtype=carrier_dtype, count=bit_height).view(np.uint8)
    ).reshape(bit_height, 8 * byte_depth)

    carrier_bits[:, 8 * byte_depth - num_lsb: 8 * byte_depth] = payload_bits.reshape(
        bit_height, num_lsb
    )

    ret = np.packbits(carrier_bits).tobytes()
    return ret if truncate else ret + carrier[byte_depth * bit_height:]


def lsb_deinterleave_bytes(carrier, num_bits, num_lsb, byte_depth=1):
    """
    Deinterleave num_bits bits from the num_lsb LSBs of carrier.
    :carrier: carrier bytes
    :num_bits: number of num_bits to retrieve
    :num_lsb: number of least significant bits to use
    :byte_depth: byte depth of carrier values
    :return: The deinterleaved bytes
    """

    plen = roundup(num_bits / num_lsb)
    carrier_dtype = byte_depth_to_dtype[byte_depth]
    payload_bits = np.unpackbits(
        np.frombuffer(carrier, dtype=carrier_dtype, count=plen).view(np.uint8)
    ).reshape(plen, 8 * byte_depth)[:, 8 * byte_depth - num_lsb: 8 * byte_depth]
    return np.packbits(payload_bits).tobytes()[: num_bits // 8]