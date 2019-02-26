#!/bin/bash

function check() {
	PRG="$1"
	which $PRG 1> /dev/null 2> /dev/null
	if [ $? -ne 0 ]; then
		echo "$PRG is not available" > /dev/stderr
		exit 1
	fi
}

function checkall() {
	check jam
	check git
	check curl
	check pkg-config
	check unzip
	check sed
	check tar
}

function downloaddependencies() {
	if [ ! -f openssl-1.0.1t.tar.gz ]; then
		curl -L -O https://www.openssl.org/source/old/1.0.1/openssl-1.0.1t.tar.gz
	fi
	if [ ! -f freetype-2.3.9.tar.bz2 ]; then
		curl -L -O https://download.savannah.gnu.org/releases/freetype/freetype-old/freetype-2.3.9.tar.bz2
	fi
}

function builddependencies() {
	if [ ! -d openssl-1.0.1t ]; then
		tar zxvf openssl-1.0.1t.tar.gz
	fi
	if [ ! -e openssl-1.0.1t/installed/lib/libssl.a ]; then
		run pushd openssl-1.0.1t 1> /dev/null 2> /dev/null
		run ./config --prefix=$PWD/installed
		run make -j10
		run make install
		run popd 1> /dev/null 2> /dev/null
	fi
	OPENSSLPKGPATH=$PWD/openssl-1.0.1t/installed/lib/pkgconfig
	
	
	if [ ! -d freetype-2.3.9 ]; then
		tar jxvf freetype-2.3.9.tar.bz2
	fi
	if [ ! -e freetype-2.3.9/installed/lib/pkgconfig/freetype2.pc ]; then
		run pushd freetype-2.3.9 1> /dev/null 2> /dev/null
		run ./configure --prefix=$PWD/installed
		run make -j10
		run make install
		run popd 1> /dev/null 2> /dev/null
	fi
	FREETYPEPATH=$PWD/freetype-2.3.9/installed/lib/pkgconfig
	FREETYPEINCDIR=$PWD/freetype-2.3.9/include

	if [ ! -x freetype-config ]; then
		cat > freetype-config <<-EOF
		#!/bin/bash
	
		while [ \$# -gt 0 ]; do
			ARG="\$1"
			shift
	
			if [ "\$ARG" = "--cflags" ]; then
				pkg-config freetype2 --cflags
			elif [ "\$ARG" = "--libs" ]; then
				pkg-config freetype2 --libs
			fi
		done
		EOF
		chmod 755 freetype-config
	fi
	NEWPATHDIR=$PWD
}

function clonemupdf() {
	if [ ! -f mupdf-thirdparty-2012-08-14.zip ]; then
		curl -L -O https://mupdf.com/downloads/archive/mupdf-thirdparty-2012-08-14.zip
	fi
	if [ ! -f mupdf-thirdparty-2011-02-24.zip ]; then
		curl -L -O https://mupdf.com/downloads/archive/mupdf-thirdparty-2011-02-24.zip
	fi
	if [ ! -f mupdf-0.7-thirdparty.zip ]; then
		curl -L -O https://mupdf.com/downloads/archive/mupdf-0.7-thirdparty.zip
	fi
	if [ ! -d mupdf.git ]; then
		run git clone --recursive git://git.ghostscript.com/mupdf.git mupdf.git
		run git clone git://git.ghostscript.com/thirdparty/glfw.git mupdf.git/thirdparty/glfw
	fi
}

function createsymlinks() {
	if [ ! -L thirdparty-curl.git ]; then run ln -s mupdf.git/thirdparty/curl thirdparty-curl.git; fi
	if [ ! -L thirdparty-freeglut.git ]; then run ln -s mupdf.git/thirdparty/freeglut thirdparty-freeglut.git; fi
	if [ ! -L thirdparty-freetype2.git ]; then run ln -s mupdf.git/thirdparty/freetype thirdparty-freetype2.git; fi
	if [ ! -L thirdparty-lcms2.git ]; then run ln -s mupdf.git/thirdparty/lcms2 thirdparty-lcms2.git; fi
	if [ ! -L thirdparty-harfbuzz.git ]; then run ln -s mupdf.git/thirdparty/harfbuzz thirdparty-harfbuzz.git; fi
	if [ ! -L jbig2dec.git ]; then run ln -s mupdf.git/thirdparty/jbig2dec jbig2dec.git; fi
	if [ ! -L thirdparty-libjpeg.git ]; then run ln -s mupdf.git/thirdparty/libjpeg thirdparty-libjpeg.git; fi
	if [ ! -L thirdparty-openjpeg.git ]; then run ln -s mupdf.git/thirdparty/openjpeg thirdparty-openjpeg.git; fi
	if [ ! -L thirdparty-zlib.git ]; then run ln -s mupdf.git/thirdparty/zlib thirdparty-zlib.git; fi
	if [ ! -L thirdparty-glfw.git ]; then run ln -s mupdf.git/thirdparty/glfw thirdparty-glfw.git; fi
	if [ ! -L mujs.git ]; then run ln -s mupdf.git/thirdparty/mujs mujs.git; fi
}

function checkoutversions() {
	for tag in 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.7a 1.8 1.9 1.9a 1.10 1.10a 1.11 1.11.1 1.12.0 1.13.0 1.14.0; do
		if [ -d ${tag}/.git ]; then
			continue
		fi
	
		run git clone --quiet --recursive mupdf.git ${tag}
		run rm -rf ${tag}/[a-zA-Z0-9]*
		run pushd ${tag} 1> /dev/null 2> /dev/null
		run git checkout --quiet ${tag}
		run git reset --quiet --hard HEAD
		if [ -f .gitmodules ]; then
			run git submodule update --quiet --recursive --init 
		fi
		run popd 1> /dev/null 2> /dev/null
	done
	for tag in 1.1 1.0; do
		if [ -d ${tag}/thirdparty -a mupdf-thirdparty-2012-08-14.zip ]; then
			continue
		fi
	
		run pushd ${tag} 1> /dev/null 2> /dev/null
		unzip -q ../mupdf-thirdparty-2012-08-14.zip
		run popd 1> /dev/null 2> /dev/null
	done
	for tag in 0.9 0.8; do
		if [ -d ${tag}/thirdparty -a mupdf-thirdparty-2011-02-24.zip ]; then
			continue
		fi
	
		run pushd ${tag} 1> /dev/null 2> /dev/null
		unzip -q ../mupdf-thirdparty-2011-02-24.zip
		run popd 1> /dev/null 2> /dev/null
	done
	for tag in 0.7 0.6; do
		if [ -d ${tag}/thirdparty -a mupdf-0.7-thirdparty.zip ]; then
			continue
		fi
	
		run pushd ${tag} 1> /dev/null 2> /dev/null
		unzip -q ../mupdf-0.7-thirdparty.zip
		run popd 1> /dev/null 2> /dev/null
	done

	if grep -q '^LIBS.*-ljbig2dec -lopenjpeg.*$' 0.6/Makerules; then
		sed -ie 's,^\(LIBS.*\) -ljbig2dec -lopenjpeg\(.*\)$,\1\2,' 0.6/Makerules
	fi
}

function run() {
	$*
	if [ $? -ne 0 ]; then echo "$* failed"; exit 1; fi
}

function run_pkgconfig() {
	echo "FREETYPECC=\"$(PKG_CONFIG_PATH=$OPENSSLPKGPATH:$FREETYPEPATH pkg-config --cflags freetype2) -I$FREETYPEINCDIR -DFT2_BUILD_LIBRARY\" PKG_CONFIG_PATH=$OPENSSLPKGPATH:$FREETYPEPATH XLIBS=-ldl $*"
	FREETYPECC="$(PKG_CONFIG_PATH=$OPENSSLPKGPATH:$FREETYPEPATH pkg-config --cflags freetype2) -I$FREETYPEINCDIR -DFT2_BUILD_LIBRARY" PKG_CONFIG_PATH=$OPENSSLPKGPATH:$FREETYPEPATH XLIBS=-ldl $*
	if [ $? -ne 0 ]; then echo "FREETYPECC=\"$(PKG_CONFIG_PATH=$OPENSSLPKGPATH:$FREETYPEPATH pkg-config --cflags freetype2) -I$FREETYPEINCDIR\" PKG_CONFIG_PATH=$OPENSSLPKGPATH:$FREETYPEPATH XLIBS=-ldl $* failed"; exit 1; fi
}

function buildmupdf() {
	for tag in 1.14.0 1.13.0 1.12.0 1.11.1 1.11; do
		if [ ! -d ${tag} ]; then
			echo "${tag} missing"
			exit 1
		fi
		if [ ! -f ${tag}/Makefile ]; then
			echo "no way to build ${tag}"
			exit 1
		fi
		if [ -f ${tag}/build/debug/mutool ]; then
			continue
		fi
	
		run pushd ${tag} 1> /dev/null 2> /dev/null
		run make -j10 build=debug
		run popd 1> /dev/null 2> /dev/null
	done
	for tag in 1.10a 1.10 1.9a 1.9 1.8 1.7a 1.7 1.6 1.5 1.4 1.3 1.2 1.1 1.0 0.9 0.8 0.7 0.6; do
		if [ ! -d ${tag} ]; then
			echo "${tag} missing"
			exit 1
		fi
		if [ ! -f ${tag}/Makefile ]; then
			echo "no way to build ${tag}"
			exit 1
		fi
		if [ -f ${tag}/build/debug/mutool -o -f ${tag}/build/debug/mudraw -o -f ${tag}/build/debug/pdfdraw ]; then
			continue
		fi
	
		run pushd ${tag} 1> /dev/null 2> /dev/null
		run_pkgconfig make -j10 build=debug
		run popd 1> /dev/null 2> /dev/null
	done
	for tag in 0.5 0.4 0.3 0.2 0.1; do
		if [ ! -d ${tag} ]; then
			echo "${tag} missing"
			exit 1
		fi
		if [ ! -f ${tag}/Jamfile ]; then
			echo "no way to build ${tag}"
			exit 1
		fi
		if [ -f ${tag}/build/*debug/pdfdraw -o -f ${tag}/build/*debug/mupdftool -o -f ${tag}/build/*debug/pdfdebug ]; then
			continue
		fi
	
		run pushd ${tag} 1> /dev/null 2> /dev/null
		run_pkgconfig jam
		run popd 1> /dev/null 2> /dev/null
	done
}

checkall
downloaddependencies
builddependencies
clonemupdf
createsymlinks
checkoutversions
buildmupdf
