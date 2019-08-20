%define major 1
%define libname %mklibname %{name} %{major}
%define devname %mklibname %{name} -d

%global optflags %{optflags} -O3

# (tpg) enable PGO build
%ifnarch %{ix86} riscv64
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	Extremely powerful file compression utility
Name:		zstd
Version:	1.4.3
Release:	1
License:	BSD
Group:		Archiving/Compression
URL:		https://github.com/facebook/zstd
Source0:	https://github.com/facebook/zstd/archive/v%{version}/%{name}-%{version}.tar.gz
Patch0:		zstd-1.3.4-multi-thread-default.patch
BuildRequires:	pkgconfig(liblz4)
BuildRequires:	pkgconfig(liblzma)
BuildRequires:	pkgconfig(zlib)
BuildRequires:	meson
BuildRequires:	ninja

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
Obsoletes:	%{mklibname %{name} -d -s} < 1.3.8-3
Provides:	%{mklibname %{name} -d -s} = 1.3.8-3

%description -n %{devname}
Header files of zstd functions, for developing apps which
will use the zstd library.

%package -n %{sdevname}
Summary:	Static libraries for zstd
Group:		Development/C
Requires:	%{devname} = %{version}-%{release}

%description -n	%{sdevname}
Static library for zstd.

%prep
%autosetup -p1

%build
%setup_compile_flags

%if %{with pgo}
CFLAGS_PGO="%{optflags} -fprofile-instr-generate"
CXXFLAGS_PGO="%{optflags} -fprofile-instr-generate"
FFLAGS_PGO="$CFLAGS_PGO"
FCFLAGS_PGO="$CFLAGS_PGO"
LDFLAGS_PGO="%{ldflags} -fprofile-instr-generate"
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
export LD_LIBRARY_PATH="$(pwd)"
%define _vpath_builddir pgo
cd build/meson
mkdir pgo
CFLAGS="${CFLAGS_PGO}" CXXFLAGS="${CXXFLAGS_PGO}" FFLAGS="${FFLAGS_PGO}" FCFLAGS="${FCFLAGS_PGO}" LDFLAGS="${LDFLAGS_PGO}" CC="%{__cc}" %meson -Dbuild_programs=true -Dbuild_contrib=true -Dzlib=enabled -Dlzma=enabled -Dlz4=enabled
%meson_build

./pgo/programs/zstd -b19i1
./pgo/programs/zstd -b16i1
./pgo/programs/zstd -b9i2
./pgo/programs/zstd -b
./pgo/programs/zstd -b7i2
./pgo/programs/zstd -b5

unset LD_LIBRARY_PATH
unset LLVM_PROFILE_FILE
llvm-profdata merge --output=%{name}.profile *.profile.d
rm -f *.profile.d
cd pgo
ninja clean
cd -
rm -rf pgo
%undefine _vpath_builddir

CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
%else
cd build/meson
%endif
%meson -Dbuild_programs=true -Dbuild_contrib=true -Dzlib=enabled -Dlzma=enabled -Dlz4=enabled
%meson_build

%install
cd build/meson
%meson_install

%files
%{_bindir}/*
%{_mandir}/man1/*

%files -n %{libname}
%{_libdir}/libzstd.so.%{major}*

%files -n %{devname}
%{_libdir}/libzstd.so
%{_libdir}/pkgconfig/*
%{_includedir}/*.h
