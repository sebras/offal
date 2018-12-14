#!/usr/bin/python

import os
import sys
import struct

def parse(data, length):
	if len(data) == 0:
		raise Exception("premature end in box (expecting %d bytes, no bytes left)" % length)
	if len(data) < length:
		print("premature end in box (expecting %d bytes, finding %d bytes), parsing what's available" % (length, len(data)))
		return ([], data)
	return (data[length:], data[0:length])

def parse8(data):
	(data, value) = parse(data, 1)
	value = ord(value)
	return (data, value)

def parse16le(data):
	(data, value) = parse(data, 2)
	value  = struct.unpack(">H", value)[0] 
	return (data, value)

def parse16be(data):
	(data, value) = parse(data, 2)
	value  = struct.unpack(">H", value)[0] 
	return (data, value)

def parse32le(data):
	(data, value) = parse(data, 4)
	value  = struct.unpack(">I", value)[0] 
	return (data, value)

def parse32be(data):
	(data, value) = parse(data, 4)
	value  = struct.unpack(">I", value)[0] 
	return (data, value)

def parsearray(data, length):
	s = ""
	for i in range(length):
		s = s + "%02x " % ord(data[i])
	s = "[" + s[:-1] + "]"
	return (data[length:], s)

def parsestring(data, length):
	s = ""
	for i in range(length):
		v = ord(data[i])
		if v < 32:
			continue
		s = s + chr(v)
	return (data[length:], s)

def parseheader(data):
        (data, byteorder) = parse16(data)
        print "hdr.byteorder = %04x" % byteorder

	if byteorder == 0x4949:
		(data, magic) = parse16le(data)
		(data, ifdoffset) = parse32le(data)
	elif byteorder == 0x4d4d:
		(data, magic) = parse16be(data)
		(data, ifdoffset) = parse32be(data)
	else
		raise Exception("unknown byteorder");

	print "hdr.magic = %04x" % magic
	print "hdr.ifdoffset = %04x" % ifdoffset


for path in sys.argv[1:]:
	with open(path, "rb") as f:
		data = f.read()

                alldata = data

                data = parseheader(data)
