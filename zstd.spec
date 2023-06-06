# zstd is used by mesa, mesa is used by wine
%ifarch %{x86_64}
%bcond_without compat32
%else
%bcond_with compat32
%endif

%define major 1
%define oldlibname %mklibname %{name} 1
%define libname %mklibname %{name}
%define devname %mklibname %{name} -d
# static libraries are used by qemu. Please don't disable them.
%define sdevname %mklibname %{name} -d -s
%define oldlib32name lib%{name}1
%define lib32name lib%{name}
%define dev32name lib%{name}-devel
%define sdev32name lib%{name}-static-devel

%global optflags %{optflags} -O3

# (tpg) use LLVM/polly for polyhedra optimization and automatic vector code generation
%define pollyflags -mllvm -polly -mllvm -polly-position=early -mllvm -polly-parallel=true -fopenmp -fopenmp-version=50 -mllvm -polly-dependences-computeout=5000000 -mllvm -polly-detect-profitability-min-per-loop-insts=40 -mllvm -polly-tiling=true -mllvm -polly-prevect-width=256 -mllvm -polly-vectorizer=stripmine -mllvm -polly-omp-backend=LLVM -mllvm -polly-num-threads=0 -mllvm -polly-scheduling=dynamic -mllvm -polly-scheduling-chunksize=1 -mllvm -polly-invariant-load-hoisting -mllvm -polly-loopfusion-greedy -mllvm -polly-run-inliner -mllvm -polly-run-dce -mllvm -polly-enable-delicm=true -mllvm -extra-vectorizer-passes -mllvm -enable-cond-stores-vec -mllvm -slp-vectorize-hor-store -mllvm -enable-loopinterchange -mllvm -enable-loop-distribute -mllvm -enable-unroll-and-jam -mllvm -enable-loop-flatten -mllvm -interleave-small-loop-scalar-reduction -mllvm -unroll-runtime-multi-exit -mllvm -aggressive-ext-opt

# (tpg) enable PGO build
%if %{cross_compiling}
%bcond_with pgo
%else
%bcond_without pgo
%endif

Summary:	Extremely powerful file compression utility
Name:		zstd
Version:	1.5.5
Release:	1
License:	BSD
Group:		Archiving/Compression
URL:		https://github.com/facebook/zstd
Source0:	https://github.com/facebook/zstd/archive/v%{version}/%{name}-%{version}.tar.gz
Requires:	%{libname} = %{EVRD}
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
%rename %{oldlibname}

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
%rename %{oldlib32name}

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

# Don't use obsolete standards
# https://github.com/facebook/zstd/issues/3163
sed -i -e 's,c99,gnu2a,g' build/cmake/CMakeModules/AddZstdCompilationFlags.cmake

%build
%set_build_flags

%if %{with compat32}
cd build/cmake
%cmake32 \
	-DZSTD_BUILD_CONTRIB:BOOL=OFF -DZSTD_LEGACY_SUPPORT:BOOL=ON -DZSTD_LZ4_SUPPORT:BOOL=ON -DZSTD_LZMA_SUPPORT:BOOL=ON -DZSTD_PROGRAMS_LINK_SHARED:BOOL=ON -DZSTD_ZLIB_SUPPORT:BOOL=ON -DZSTD_MULTITHREAD_SUPPORT:BOOL=ON -DCMAKE_ASM_FLAGS_RELWITHDEBINFO="%{optflags} -m32" \
	-G Ninja
cd ..
%ninja_build -C build32
cd ../..
%endif

%if %{with pgo}
cd build/cmake
CFLAGS="%{optflags} -fprofile-generate -mllvm -vp-counters-per-site=100 %{pollyflags}" \
CXXFLAGS="%{optflags} -fprofile-generate -mllvm -vp-counters-per-site=100 %{pollyflags}" \
LDFLAGS="%{build_ldflags} -fprofile-generate -mllvm -vp-counters-per-site=100" \
%cmake \
	-DZSTD_BUILD_CONTRIB:BOOL=ON \
	-DZSTD_LEGACY_SUPPORT:BOOL=ON \
	-DZSTD_LZ4_SUPPORT:BOOL=ON \
	-DZSTD_LZMA_SUPPORT:BOOL=ON \
	-DZSTD_PROGRAMS_LINK_SHARED:BOOL=ON \
	-DZSTD_ZLIB_SUPPORT:BOOL=ON \
	-DZSTD_MULTITHREAD_SUPPORT:BOOL=ON \
	-G Ninja

cd ..
export LD_LIBRARY_PATH="$(pwd)/build/lib"

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
llvm-profdata merge --output=%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profile.d
rm -rf build

CFLAGS="%{optflags} -fprofile-use=$PROFDATA %{pollyflags}" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA %{pollyflags}" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA" \
%else
cd build/cmake
%endif
%cmake \
%if %{cross_compiling}
	-DZSTD_BUILD_CONTRIB:BOOL=OFF \
%else
	-DZSTD_BUILD_CONTRIB:BOOL=ON \
%endif
	-DZSTD_LEGACY_SUPPORT:BOOL=ON \
	-DZSTD_LZ4_SUPPORT:BOOL=ON \
	-DZSTD_LZMA_SUPPORT:BOOL=ON \
	-DZSTD_PROGRAMS_LINK_SHARED:BOOL=ON \
	-DZSTD_ZLIB_SUPPORT:BOOL=ON \
	-DZSTD_MULTITHREAD_SUPPORT:BOOL=ON \
	-G Ninja

%ninja_build

%install
cd build/cmake
%if %{with compat32}
%ninja_install -C build32
%endif
%ninja_install -C build
%if ! %{cross_compiling}
install -m 755 build/contrib/pzstd/pzstd %{buildroot}%{_bindir}/
%endif

%files
%{_bindir}/*
%doc %{_mandir}/man1/*

%files -n %{libname}
%{_libdir}/libzstd.so.%{major}*

%files -n %{devname}
%{_libdir}/libzstd.so
%{_libdir}/pkgconfig/*
%{_includedir}/*.h
%dir %{_libdir}/cmake/zstd
%{_libdir}/cmake/zstd/*.cmake
%if ! %{cross_compiling}
%doc %{_docdir}/zstd
%endif

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
