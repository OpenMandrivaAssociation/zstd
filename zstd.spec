# zstd is used by mesa, mesa is used by wine
%ifarch %{x86_64}
%bcond_without compat32
%else
%bcond_with compat32
%endif

%define major 1
%define libname %mklibname %{name} %{major}
%define devname %mklibname %{name} -d
# static libraries are used by qemu. Please don't disable them.
%define sdevname %mklibname %{name} -d -s
%define lib32name lib%{name}%{major}
%define dev32name lib%{name}-devel
%define sdev32name lib%{name}-static-devel

%global optflags %{optflags} -Ofast

# (tpg) enable PGO build
%ifnarch %{ix86} riscv64
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	Extremely powerful file compression utility
Name:		zstd
Version:	1.4.9
Release:	1
License:	BSD
Group:		Archiving/Compression
URL:		https://github.com/facebook/zstd
Source0:	https://github.com/facebook/zstd/archive/v%{version}/%{name}-%{version}.tar.gz
BuildRequires:	pkgconfig(liblz4)
BuildRequires:	pkgconfig(liblzma)
BuildRequires:	pkgconfig(zlib)
BuildRequires:	cmake
BuildRequires:	ninja
%if %{with compat32}
BuildRequires:	devel(liblz4)
BuildRequires:	devel(liblzma)
BuildRequires:	devel(libz)
%endif

%description
Compression algorithm and implementation designed to
scale with modern hardware and compress smaller and
faster. Zstandard combines recent compression
breakthroughs, like Finite State Entropy, with a
performance-first design — and then optimizes the
implementation for the unique properties of modern CPUs.

%package -n %{libname}
Summary:	Libraries for developing apps which will use zstd
Group:		System/Libraries

%description -n %{libname}
Library of zstd functions, for developing apps which will use the
zstd library.

%package -n %{devname}
Summary:	Header files for developing apps which will use zstd
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}

%description -n %{devname}
Header files of zstd functions, for developing apps which
will use the zstd library.

%package -n %{sdevname}
Summary:	Static libraries for zstd
Group:		Development/C
Requires:	%{devname} = %{version}-%{release}

%description -n	%{sdevname}
Static library for zstd.

%if %{with compat32}
%package -n %{lib32name}
Summary:	Libraries for developing apps which will use zstd (32-bit)
Group:		System/Libraries

%description -n %{lib32name}
Library of zstd functions, for developing apps which will use the
zstd library.

%package -n %{dev32name}
Summary:	Header files for developing apps which will use zstd (32-bit)
Group:		Development/C
Requires:	%{devname} = %{version}-%{release}
Requires:	%{lib32name} = %{version}-%{release}

%description -n %{dev32name}
Header files of zstd functions, for developing apps which
will use the zstd library.

%package -n %{sdev32name}
Summary:	Static libraries for zstd (32-bit)
Group:		Development/C
Requires:	%{dev32name} = %{version}-%{release}

%description -n	%{sdev32name}
Static library for zstd.
%endif

%prep
%autosetup -p1
# Get rid of -L/usr/lib insanity
sed -i -e 's,-L\${libdir} ,,g' lib/*.pc.in
sed -i -e '/^Cflags:/d' lib/*.pc.in

%build
%set_build_flags

%if %{with compat32}
cd build/cmake
%cmake32 \
	-DZSTD_BUILD_CONTRIB:BOOL=OFF -DZSTD_LEGACY_SUPPORT:BOOL=ON -DZSTD_LZ4_SUPPORT:BOOL=ON -DZSTD_LZMA_SUPPORT:BOOL=ON -DZSTD_PROGRAMS_LINK_SHARED:BOOL=ON -DZSTD_ZLIB_SUPPORT:BOOL=ON -DZSTD_MULTITHREAD_SUPPORT:BOOL=ON \
	-G Ninja
cd ..
%ninja_build -C build32
cd ../..
%endif

%if %{with pgo}
CFLAGS_PGO="%{optflags} -fprofile-instr-generate"
CXXFLAGS_PGO="%{optflags} -fprofile-instr-generate"
FFLAGS_PGO="$CFLAGS_PGO"
FCFLAGS_PGO="$CFLAGS_PGO"
LDFLAGS_PGO="%{ldflags} -fprofile-instr-generate"
cd build/cmake
CFLAGS="${CFLAGS_PGO}" CXXFLAGS="${CXXFLAGS_PGO}" FFLAGS="${FFLAGS_PGO}" FCFLAGS="${FCFLAGS_PGO}" LDFLAGS="${LDFLAGS_PGO}" CC="%{__cc}" %cmake -DZSTD_BUILD_CONTRIB:BOOL=ON -DZSTD_LEGACY_SUPPORT:BOOL=ON -DZSTD_LZ4_SUPPORT:BOOL=ON -DZSTD_LZMA_SUPPORT:BOOL=ON -DZSTD_PROGRAMS_LINK_SHARED:BOOL=ON -DZSTD_ZLIB_SUPPORT:BOOL=ON -DZSTD_MULTITHREAD_SUPPORT:BOOL=ON -G Ninja
cd ..
export LD_LIBRARY_PATH="$(pwd)/build/lib"
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
%ninja_build -C build

cp %{S:0} .
gunzip *.tar.gz
./build/programs/zstd -b19i1
./build/programs/zstd -b16i1
./build/programs/zstd -b9i2
./build/programs/zstd -b
./build/programs/zstd -b7i2
./build/programs/zstd -b5
./build/programs/zstd --rm -19 *.tar
./build/programs/zstd -d --rm *.tar.zst
./build/programs/zstd --rm --ultra -22 *.tar
./build/programs/zstd -d --rm *.tar.zst
./build/contrib/pzstd/pzstd --rm -19 *.tar
./build/contrib/pzstd/pzstd -d --rm *.tar.zst
./build/contrib/pzstd/pzstd --rm --ultra -22 *.tar
./build/contrib/pzstd/pzstd -d --rm *.tar.zst
rm *.tar

unset LD_LIBRARY_PATH
unset LLVM_PROFILE_FILE
llvm-profdata merge --output=%{name}.profile *.profile.d
rm -f *.profile.d
rm -rf build

CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
%else
cd build/cmake
%endif
%cmake -DZSTD_BUILD_CONTRIB:BOOL=ON -DZSTD_LEGACY_SUPPORT:BOOL=ON -DZSTD_LZ4_SUPPORT:BOOL=ON -DZSTD_LZMA_SUPPORT:BOOL=ON -DZSTD_PROGRAMS_LINK_SHARED:BOOL=ON -DZSTD_ZLIB_SUPPORT:BOOL=ON -DZSTD_MULTITHREAD_SUPPORT:BOOL=ON -G Ninja
%ninja_build

%install
cd build/cmake
%if %{with compat32}
%ninja_install -C build32
%endif
%ninja_install -C build
install -m 755 build/contrib/pzstd/pzstd %{buildroot}%{_bindir}/

%files
%{_bindir}/*
%{_mandir}/man1/*

%files -n %{libname}
%{_libdir}/libzstd.so.%{major}*

%files -n %{devname}
%{_libdir}/libzstd.so
%{_libdir}/pkgconfig/*
%{_includedir}/*.h
%dir %{_libdir}/cmake/zstd
%{_libdir}/cmake/zstd/*.cmake
%doc %{_docdir}/zstd

%files -n %{sdevname}
%{_libdir}/libzstd.a

%if %{with compat32}
%files -n %{lib32name}
%{_prefix}/lib/libzstd.so.%{major}*

%files -n %{dev32name}
%{_prefix}/lib/libzstd.so
%{_prefix}/lib/pkgconfig/*
%dir %{_prefix}/lib/cmake/zstd
%{_prefix}/lib/cmake/zstd/*.cmake

%files -n %{sdev32name}
%{_prefix}/lib/libzstd.a
%endif
