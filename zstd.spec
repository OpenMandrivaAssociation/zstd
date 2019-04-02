%define major 1
%define libname %mklibname %{name} %{major}
%define devname %mklibname %{name} -d
%define sdevname %mklibname %{name} -d -s

%global optflags %{optflags} -O3

# (tpg) enable PGO build
%bcond_without pgo

Summary:	Extremely powerful file compression utility
Name:		zstd
Version:	1.3.8
Release:	3
License:	BSD
Group:		Archiving/Compression
URL:		https://github.com/facebook/zstd
Source0:	https://github.com/facebook/zstd/archive/%{name}-%{version}.tar.gz
Patch0:		zstd-1.3.4-multi-thread-default.patch
BuildRequires:	pkgconfig(liblz4)
BuildRequires:	pkgconfig(liblzma)
BuildRequires:	pkgconfig(zlib)

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

%description -n	%{libname}
Library of zstd functions, for developing apps which will use the
zstd library.

%package -n %{devname}
Summary:	Header files for developing apps which will use zstd
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}

%description -n	%{devname}
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
%make_build CC=%{__cc} CFLAGS="${CFLAGS_PGO} -std=c11" LDFLAGS="${LDFLAGS_PGO}" PREFIX="%{_prefix}" LIBDIR="%{_libdir}" check
unset LD_LIBRARY_PATH
unset LLVM_PROFILE_FILE
llvm-profdata merge --output=%{name}.profile *.profile.d
rm -f *.profile.d
make clean
export CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)"
export CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)"
export LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile)"
%endif

%make_build CC=%{__cc} CFLAGS="${CFLAGS} -std=c11" LDFLAGS="${LDFLAGS}" PREFIX="%{_prefix}" LIBDIR="%{_libdir}"
%make_build CC=%{__cc} CFLAGS="${CFLAGS} -std=c11" LDFLAGS="${LDFLAGS}" PREFIX="%{_prefix}" LIBDIR="%{_libdir}" -C 'contrib/pzstd'

# (tpg) build zlibwrapper
# %make zlibwrapper CC=%{__cc} CFLAGS="%{optflags} -std=c11" PREFIX="%{_prefix}" LIBDIR="%{_libdir}"

%install
%make_install PREFIX="%{_prefix}" LIBDIR="%{_libdir}"

install -D -m755 contrib/pzstd/pzstd %{buildroot}%{_bindir}/pzstd
install -D -m644 programs/%{name}.1 %{buildroot}/%{_mandir}/man1/p%{name}.1

%files
%{_bindir}/*
%{_mandir}/man1/*

%files -n %{libname}
%{_libdir}/libzstd.so.%{major}*

%files -n %{devname}
%{_libdir}/libzstd.so
%{_libdir}/pkgconfig/*
%{_includedir}/*.h

%files -n %{sdevname}
%{_libdir}/libzstd.a
