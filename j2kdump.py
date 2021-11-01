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

def parse16(data):
	(data, value) = parse(data, 2)
	value  = struct.unpack(">H", value)[0]
	return (data, value)

def parse32(data):
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

def parsebox(data):
	#print "parsing box with %d bytes left" % len(data)
	(data, length) = parse32(data)
	#print "\tlength = %d" % length

	#print "parsing box type with %d bytes left" % len(data)
	(data, boxtype) = parse(data, 4)
	#print "\ttype = \"%s\"" % boxtype

	if length >= 8:
		#print "parsing %d byte box data with %d bytes left" % (length - 8, len(data))
		(data, boxdata) = parse(data, length - 8)
	else:
		boxdata = data

	return (data, boxtype, boxdata)

def parsejp2signaturebox(data):
	#print "jp2 signature box (%d bytes)" % len(data)
	if len(data) != 4:
		raise Exception("unexpected jp2 signature box length")

	reference = "\x0d\x0a\x87\x0a"

	(data, signature) = parse(data, 4)
	for i in range(len(signature)):
		if reference[i] != signature[i]:
			raise Exception("signature difference at %d (%02x vs %02x" % (i, reference[i], signature[i]))

	(data, signature) = parsearray(signature, 4)
	print "jp  .contents = %s" % signature

	return data

def parsefiletype(data):
	#print "file type box (%d bytes)" % len(data)

	(data, BR) = parse(data, 4)
	print "ftyp.BR = %s" % BR

	(data, MinV) = parse32(data)
	print "ftyp.MinV = %d" % MinV

	index = 0
	while len(data) >= 4:
		(data, CL) = parse(data, 4)
		print "ftyp.CL%d = %s" % (index, CL)
		index = index + 1

	return data

def parsecomponentdefinitionbox(data):
	#print "component definition box (%d bytes)" % len(data)
	if len(data) < 2:
		raise Exception("premature end in component definition box")

	(data, N) = parse16(data)
	print "cdef.N = %d" % N

	if len(data) < (2 + 2 + 2) * N:
		raise Exception("premature end in component definition box")

	for i in range(N):
		(data, Cn) = parse16(data)
		print "cdef.Cn[%d] = %d" % (i, Cn)
		(data, Typ) = parse16(data)
		print "cdef.Typ[%d] = %d" % (i, Typ)
		(data, Asoc) = parse16(data)
		print "cdef.Asoc[%d] = %d" % (i, Asoc)

	return data

def parsejp2headerbox(data):
	#print "jp2 header box (%d bytes)" % len(data)

	while len(data) > 0:
		(data, boxtype, boxdata) = parsebox(data)
		# missing: bpcc, pclr
		if boxtype == "\x69\x68\x64\x72":
			parseimageheaderbox(boxdata)
		elif boxtype == "\x63\x6f\x6c\x72":
			parsecolorspecificationbox(boxdata)
		elif boxtype == "\x72\x65\x73\x20":
			parseresolutionbox(boxdata)
		elif boxtype == "\x63\x64\x65\x66":
			parsecomponentdefinitionbox(boxdata)
		else:
			print "ignoring unknown jp2 header box subbox of type: %s" % boxtype

	return data

def parseimageheaderbox(data):
	#print "image header box (%d bytes)" % len(data)
	if len(data) < 14:
		raise Exception("premature end in image header box")

	(data, HEIGHT) = parse32(data)
	print "ihdr.HEIGHT = %d" % HEIGHT

	(data, WIDTH) = parse32(data)
	print "ihdr.WIDTH = %d" % WIDTH

	(data, NC) = parse16(data)
	print "ihdr.components = %d" % NC

	(data, BPC) = parse8(data)
	if BPC == 255:
		print "ihdr.BPC = varies"
	else:
		if ((BPC >> 7) & 0x1) == 1:
			sign = "signed"
		else:
			sign = "unsigned"
		bpc = (BPC & 0x7f) + 1
		print "ihdr.BPC = %d (%d %s bits per components)" % (BPC, bpc, sign)

	(data, C) = parse8(data)
	print "ihdr.C = %d" % C

	(data, UnkC) = parse8(data)
	print "ihdr.UnkC = %d" % UnkC

	(data, IPR) = parse8(data)
	print "ihdr.IPR = %d" % IPR

	return data

def parsecolorspecificationbox(data):
	#print "color specification box (%d bytes)" % len(data)

	(data, METH) = parse8(data)
	if METH == 1:
		print "colr.METH = %d (enumerated colorspace)" % METH
	elif METH == 2:
		print "colr.METH = %d (Restriced ICC profile)" % METH
	else:
		raise Exception("unknown colorspace specification method")

	(data, PREC) = parse8(data)
	print "colr.PREC = %d" % PREC

	(data, APPROX) = parse8(data)
	print "colr.APPROX = %d" % APPROX

	if METH == 1:
		(data, EnumCS) = parse32(data)
		if EnumCS == 16:
			print "colr.EnumCS = %d (sRGB)" % EnumCS
		elif EnumCS == 17:
			print "colr.EnumCS = %d (grayscale)" % EnumCS
		elif EnumCS == 18:
			print "colr.EnumCS = %d (sYCC)" % EnumCS
		else:
			raise Exception("unknown enumerated colorsdpace")
	elif METH == 2:
		(data, icclength) = parse32(data)
		print "colr.icclength = %d" % icclength

		(data, _) = parse(data, icclength - 4)

	return data

def parsecaptureresolutionbox(data):
	(data, VRcN) = parse16(data)
	print "resc.VRcN = %d" % VRcN

	(data, VRcD) = parse16(data)
	print "resc.VRcD = %d" % VRcD

	(data, HRcN) = parse16(data)
	print "resc.HRcN = %d" % HRcN

	(data, HRcD) = parse16(data)
	print "resc.HRcD = %d" % HRcD

	(data, VRcE) = parse8(data)
	print "resc.VRcE = %d" % VRcE

	(data, HRcE) = parse8(data)
	print "resc.HRcE = %d" % HRcE

	return data

def parsedefaultdisplayresolutionbox(data):
	#print "default display resolution box (%d bytes)" % len(data)
	if len(data) < 10:
		raise Exception("premature end in default display resolution box")

	(data, VRcN) = parse16(data)
	print "resd.VRcN = %d" % VRcN

	(data, VRcD) = parse16(data)
	print "resd.VRcD = %d" % VRcD

	(data, HRcN) = parse16(data)
	print "resd.HRcN = %d" % HRcN

	(data, HRcD) = parse16(data)
	print "resd.HRcD = %d" % HRcD

	(data, VRcE) = parse8(data)
	print "resd.VRcE = %d" % VRcE

	(data, HRcE) = parse8(data)
	print "resd.HRcE = %d" % HRcE

	return data

def parseresolutionbox(data):
	#print "jp2 resolution box (%d bytes)" % len(data)

	while len(data) > 0:
		(data, boxtype, boxdata) = parsebox(data)
		if boxtype == "\x72\x65\x73\x63":
			parsecaptureresolutionbox(boxdata)
		if boxtype == "\x72\x65\x73\x64":
			parsedefaultdisplayresolutionbox(boxdata)
		else:
			print "unknown resolution box subbox of type: %s" % boxtype

	return data

def parseuuidbox(data):
	#print "uuid box (%d bytes)" % len(data)

	(data, uuid) = parse(data, 16)
	uuidstr = ""
	for i in range(len(uuid)):
		uuidstr = uuidstr + "%02x" % ord(uuid[i])
		if i == 3 or i == 5 or i == 7 or i == 9:
			uuidstr = uuidstr + "-"
	print "uuid = %s" % uuidstr

	(data, vendordata) = parsearray(data, len(data))
	print "uuid.vendordata = %s" % vendordata

	return data

def parsestartofcodestreammarker(data):
	print "jp2c.SOC"
	return data

def parseimageandtilesizemarker(data):
	(data, Lsiz) = parse16(data)
	print "jp2c.SIZ.Lsiz = %d" % Lsiz

	(data, Rsiz) = parse16(data)
	print "jp2c.SIZ.Rsiz = %d" % Rsiz

	(data, Xsiz) = parse32(data)
	print "jp2c.SIZ.Xsiz = %d" % Xsiz

	(data, Ysiz) = parse32(data)
	print "jp2c.SIZ.Ysiz = %d" % Ysiz

	(data, XOsiz) = parse32(data)
	print "jp2c.SIZ.XOsiz = %d" % XOsiz

	(data, YOsiz) = parse32(data)
	print "jp2c.SIZ.YOsiz = %d" % YOsiz

	(data, XTsiz) = parse32(data)
	print "jp2c.SIZ.XTsiz = %d" % XTsiz

	(data, YTsiz) = parse32(data)
	print "jp2c.SIZ.YTsiz = %d" % YTsiz

	(data, XTOsiz) = parse32(data)
	print "jp2c.SIZ.XTOsiz = %d" % XTOsiz

	(data, YTOsiz) = parse32(data)
	print "jp2c.SIZ.YTOsiz = %d" % YTOsiz

	(data, Csiz) = parse16(data)
	print "jp2c.SIZ.Csiz = %d" % Csiz

	for i in range(Csiz):
		(data, Ssiz) = parse8(data)
		print "jp2c.SIZ.C%d.Ssiz = %d" % (i, Ssiz + 1)

		(data, XRsiz) = parse8(data)
		print "jp2c.SIZ.C%d.XRsiz = %d" % (i, XRsiz)

		(data, YRsiz) = parse8(data)
		print "jp2c.SIZ.C%d.YRsiz = %d" % (i, YRsiz)

	return (data, Csiz)

def parsecodingstyledefaultmarker(data):
	(data, Lcod) = parse16(data)
	print "jp2c.COD.Lcod = %d" % Lcod

	if Lcod >= 1:
		(data, Scod) = parse8(data)
		print "jp2c.COD.Scod = %d" % Scod
		Lcod = Lcod - 1

	if Lcod >= 1:
		(data, order) = parse8(data)
		print "jp2c.COD.SGcod.Progression order = %d" % order
		Lcod = Lcod - 1

	if Lcod >= 2:
		(data, layers) = parse16(data)
		print "jp2c.COD.SGcod.Number of layers = %d" % layers
		Lcod = Lcod - 2

	if Lcod >= 1:
		(data, multitransform) = parse8(data)
		print "jp2c.COD.SGcod.Multiple component transformation = %d" % multitransform
		Lcod = Lcod - 1

	if Lcod >= 1:
		(data, levels) = parse8(data)
		print "jp2c.COD.SPcod.Number of decomposition levels = %d" % levels

	if Lcod >= 1:
		(data, width) = parse8(data)
		print "jp2c.COD.SPcod.Code-block width = %d" % width

	if Lcod >= 1:
		(data, height) = parse8(data)
		print "jp2c.COD.SPcod.Code-block height = %d" % height

	if Lcod >= 1:
		(data, style) = parse8(data)
		print "jp2c.COD.SPcod.Code-block style = %d" % style

	if Lcod >= 1:
		(data, transform) = parse8(data)
		print "jp2c.COD.SPcod.Transform = %d" % transform

	if Scod & 1 == 1 and Lcod >= 1:
		(data, size) = parse8(data)
		print "jp2c.COD.SPcod.Precinct size = %d" % size

	return data

def parsequantizationdefaultmarker(data):
	(data, Lqcd) = parse16(data)
	print "jp2c.QCD.Lqcd = %d" % Lqcd

	(data, Sqcd) = parse8(data)
	print "jp2c.QCD.Sqcd = %d" % Sqcd

	(data, SPqcd) = parsearray(data, Lqcd - 3)
	print "jp2c.QCD.SPqcd = %s" % SPqcd

	return data

def parsecommentandextensionmarker(data):
	(data, Lcme) = parse16(data)
	print "jp2c.CME.Lcme = %d" % Lcme

	(data, Rcme) = parse16(data)
	print "jp2c.CME.Rcme = %d" % Rcme

	(data, Ccme) = parsestring(data, Lcme - 4)
	print "jp2c.CME.Ccme = \"%s\"" % Ccme

	return data

def parsestartoftilepartmarker(data):
	(data, Lsot) = parse16(data)
	print "jp2c.SOT.Lsot = %d" % Lsot

	(data, Isot) = parse16(data)
	print "jp2c.SOT.Isot = %d" % Isot

	(data, Psot) = parse32(data)
	print "jp2c.SOT.Psot = %d" % Psot

	(data, TPsot) = parse8(data)
	print "jp2c.SOT.TPsot = %d" % TPsot

	(data, TNsot) = parse8(data)
	print "jp2c.SOT.TNsot = %d" % TNsot

	if Psot == 0:
		return (data, 0)
	else:
		return (data, Psot - 12)

def parsestartofdatamarker(data, length):
	print "jp2c.SOD.data.length = %d" % length

	if length == 0:
		return []

	(data, _) = parse(data, length - 2)
	return data

def parseendofcodestreammarker(data):
	print "jp2c.EOC"

	return data

def parsecodingstylecomponentmarker(data, Csiz):

	(data, Lcoc) = parse16(data)
	print "jp2c.COC.Lcoc = %d" % Lcoc

	if Csiz < 257:
		(data, Ccoc) = parse8(data)
	else:
		(data, Ccoc) = parse16(data)
	print "jp2c.COC.Ccoc = %d" % Ccoc

	(data, Scoc) = parse8(data)
	print "jp2c.COC.Scoc = %d" % Scoc

	if Csiz < 256:
		(data, SPcoc) = parsearray(data, Lcoc - 4)
	else:
		(data, SPcoc) = parsearray(data, Lcoc - 5)
	print "jp2c.COC.SPcoc = %s" % SPcoc

	return data

def parsestartofscanmarker(data, Csiz):
	print "jp2c.SOS"

	(data, Ls) = parse16(data)
	print "jp2c.SOS.Ls = %d" % Ls

	(data, Ns) = parse8(data)
	print "jp2c.SOS.Ns = %d" % Ns

	for i in range(Csiz):
		(data, Cs) = parse8(data)
		print "jp2c.SOS.Cs%d = %d" % (i, Cs)

		(data, TdTa) = parse8(data)
		Td = (TdTa >> 4) & 0xf
		Ta = (TdTa >> 0) & 0xf
		print "jp2c.SOS.Td%d = %d" % (i, Td)
		print "jp2c.SOS.Ta%d = %d" % (i, Ta)

	(data, Ss) = parse8(data)
	print "jp2c.SOS.Ss = %d" % Ss

	(data, Se) = parse8(data)
	print "jp2c.SOS.Se = %d" % Se

	(data, AhAl) = parse8(data)
	Ah = (AhAl >> 4) & 0xf
	Al = (AhAl >> 0) & 0xf
	print "jp3c.SOS.Ah = %d" % Ah
	print "jp2c.SOS.Al = %d" % Al

	return data

def parsereservedmarker(data):
	print "jp2c.RESERVED"

	return data

def parsequantizationcomponentmarker(data, Csiz):
	(data, Lqcc) = parse16(data)
	print "jp2c.QCC.Lqcc = %d" % Lqcc

	if Csiz < 257:
		(data, Cqcc) = parse8(data)
	else:
		(data, Cqcc) = parse16(data)
	print "jp2c.QCC.Cqcc = %s" % Cqcc

	(data, Sqcc) = parse8(data)
	print "jp2c.QCC.Sqcc = %d" % Sqcc

	if Csiz < 257:
		(data, SPqcc) = parsearray(data, Lqcc - 4)
	else:
		(data, SPqcc) = parsearray(data, Lqcc - 5)
	print "jp2c.QCC.SPqcc = %s" % SPqcc

	return data

def parseregionofinterestmarker(data, Csiz):
	(data, Lrgn) = parse16(data)
	print "jp2c.RGN.Lrgn = %d" % Lrgn

	if Csiz < 257:
		(data, Crgn) = parse8(data)
	else:
		(data, Crgn) = parse16(data)
	print "jp2c.RGN.Crgn = %s" % Crgn

	(data, Srgn) = parse8(data)
	print "jp2c.RGN.Srgn = %d" % Srgn

	if Csiz < 257:
		(data, SPrgn) = parsearray(data, Lrgn - 4)
	else:
		(data, SPrgn) = parsearray(data, Lrgn - 5)
	print "jp2c.RGN.SPrgn = %s" % SPrgn

	return data

def parseprogressionorderchangemarker(data, Csiz):
	(data, Lpoc) = parse16(data)
	print "jp2c.POC.Lpoc = %d" % Lpoc

	if Csiz < 257:
		nbr = (Lpoc - 2) / 7
	else:
		nbr = (Lpoc - 2) / 9

	for i in range(nbr):
		(data, RSpoc) = parse8(data)
		print "jp2c.POC.RSpoc%d = %d" % (i, RSpoc)

		if Csiz < 257:
			(data, CSpoc) = parse8(data)
		else:
			(data, CSpoc) = parse16(data)
		print "jp2c.POC.CSpoc%d = %s" % (i, CSpoc)

		(data, LYEpoc) = parse16(data)
		print "jp2c.POC.LYEpoc%d = %d" % (i, LYEpoc)

		(data, REpoc) = parse8(data)
		print "jp2c.POC.REpoc%d = %d" % (i, REpoc)

		if Csiz < 257:
			(data, CEpoc) = parse8(data)
		else:
			(data, CEpoc) = parse16(data)
		print "jp2c.POC.CEpoc%d = %s" % (i, CEpoc)

		(data, Ppoc) = parse8(data)
		print "jp2c.POC.Ppoc%d = %d" % (i, Ppoc)

	return data

def parsetilelengthmarker(data, Csiz):
	(data, Ltlm) = parse16(data)
	print "jp2c.TLM.Ltlm = %d" % Ltlm

	(data, Ztlm) = parse8(data)
	print "jp2c.TLM.Ztlm = %d" % Ztlm

	(data, Stlm) = parse8(data)
	print "jp2c.TLM.Stlm = %d %02x" % (Stlm, Stlm)

	if ((Stlm & 0x30) >> 4) == 0:
		ST = 0
	elif ((Stlm & 0x30) >> 4) == 1:
		ST = 1
	elif ((Stlm & 0x30) >> 4) == 2:
		ST = 2
	print "jp2c.TLM.Stlm.ST = %d" % ST

	if ((Stlm & 0x40) >> 6) == 0:
		SP = 0
	elif ((Stlm & 0x40) >> 6) == 1:
		SP = 1
	print "jp2c.TLM.Stlm.SP = %d" % SP

	if ST == 0 and SP == 0:
		parts = (Ltlm - 4) / 2
	elif ST == 1 and SP == 0:
		parts = (Ltlm - 4) / 3
	elif ST == 2 and SP == 0:
		parts = (Ltlm - 4) / 4
	elif ST == 0 and SP == 1:
		parts = (Ltlm - 4) / 4
	elif ST == 1 and SP == 1:
		parts = (Ltlm - 4) / 5
	elif ST == 2 and SP == 1:
		parts = (Ltlm - 4) / 6
	print "jp2c.TLM.Stlm.parts = %d" % parts

	for i in range(parts):
		if ST == 1:
			(data, Ttlm) = parse8(data)
			print "jp2c.TLM.Ttlm%d = %d" % (i, Ttlm)
		elif ST == 2:
			(data, Ttlm) = parse16(data)
			print "jp2c.TLM.Ttlm%d = %d" % (i, Ttlm)

		if SP == 0:
			(data, Ptlm) = parse16(data)
			print "jp2c.TLM.Ptlm%d = %d" % (i, Ptlm)
		elif SP == 1:
			(data, Ptlm) = parse32(data)
			print "jp2c.TLM.Ptlm%d = %d" % (i, Ptlm)

	return data

def parsemarker(data, done, length, Csiz):
	(data, marker) = parse16(data)

	# ITU-T T.81 ff00-ff01, ffc0-ffdf, fffe
	if marker == 0xffd9:
		done = True
		data = parseendofcodestreammarker(data)
	elif marker == 0xffda:
		data = parsestartofscanmarker(data, Csiz)
	# ITU-T T.84 fff0-fff6
	# ITU-T T.87 fff7-fff8
	# ITU-T T.800 ff4f-ff6f, ff90-ff93
	elif marker == 0xff4f:
		data = parsestartofcodestreammarker(data)
	elif marker == 0xff51:
		(data, Csiz) = parseimageandtilesizemarker(data)
	elif marker == 0xff52:
		data = parsecodingstyledefaultmarker(data)
	elif marker == 0xff53:
		data = parsecodingstylecomponentmarker(data, Csiz)
	elif marker == 0xff55:
		data = parsetilelengthmarker(data, Csiz)
	elif marker == 0xff5c:
		data = parsequantizationdefaultmarker(data)
	elif marker == 0xff5d:
		data = parsequantizationcomponentmarker(data, Csiz)
	elif marker == 0xff5e:
		data = parseregionofinterestmarker(data, Csiz)
	elif marker == 0xff5f:
		data = parseprogressionorderchangemarker(data, Csiz)
	elif marker == 0xff64:
		data = parsecommentandextensionmarker(data)
	elif marker == 0xff90:
		(data, length) = parsestartoftilepartmarker(data)
	elif marker == 0xff93:
		data = parsestartofdatamarker(data, length)
	elif marker >= 0xff30 and marker <= 0xff3f:
		data = parsereservedmarker(data)
	else:
		raise Exception("unknown marker 0x%04x with %d bytes left" % (marker, len(data)))

	return (data, done, length, Csiz);

def parsecontiguouscodestreambox(data):
	#print "continguous codestream box (%d bytes)" % len(data)

	length = 0
	done = False
	Csiz = 0

	while not done:
		(data, done, length, Csiz) = parsemarker(data, done, length, Csiz)

	return data

def hasjp2signaturebox(data):
	if len(data) < 12:
		return False

	reference = "\x00\x00\x00\x0c\x6a\x50\x20\x20\x0d\x0a\x87\x0a"
	for i in range(len(reference)):
		if reference[i] != data[i]:
			return False

	return True

for path in sys.argv[1:]:
	with open(path, "rb") as f:
		data = f.read()

		if not hasjp2signaturebox(data):
			data = parsecontiguouscodestreambox(data)
			if len(data) != 0:
				raise Exception("extraneous %d bytes of data at end of file" % len(data))
		else:
			while len(data) > 0:
				(data, boxtype, boxdata) = parsebox(data)
				# missing: prfl, jp2i, xml_, uinf
				if boxtype == "\x6a\x50\x20\x20":
					boxdata = parsejp2signaturebox(boxdata)
				elif boxtype == "\x66\x74\x79\x70":
					boxdata = parsefiletype(boxdata)
				elif boxtype == "\x6a\x70\x32\x68":
					boxdata = parsejp2headerbox(boxdata)
				elif boxtype == "\x75\x75\x69\x64":
					boxdata = parseuuidbox(boxdata)
				elif boxtype == "\x6a\x70\x32\x63":
					data = parsecontiguouscodestreambox(boxdata)
					boxdata = []
				else:
					print "ignoring unknown box of type: %s" % boxtype
					boxdata = []

				if len(boxdata) != 0:
					raise Exception("extraneous %d bytes of data at end of box" % len(boxdata))
