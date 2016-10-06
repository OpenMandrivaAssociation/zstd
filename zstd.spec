%define	major	1
%define	libname	%mklibname %{name} %{major}
%define	devname	%mklibname %{name} -d
%define	sdevname	%mklibname %{name} -d -s

Summary:	Extremely powerful file compression utility
Name:		zstd
Version:	1.1.0
Release:	1
License:	BSD
Group:		Archiving/Compression
URL:		https://code.facebook.com/posts/1658392934479273/smaller-and-faster-data-compression-with-zstandard/
Source0:	https://github.com/facebook/zstd/archive/v%{version}.tar.gz

%description
Compression algorithm and implementation designed to
scale with modern hardware and compress smaller and
faster. Zstandard combines recent compression
breakthroughs, like Finite State Entropy, with a
performance-first design — and then optimizes the
implementation for the unique properties of modern CPUs.

%package -n	%{libname}
Summary:	Libraries for developing apps which will use zstd
Group:		System/Libraries

%description -n	%{libname}
Library of zstd functions, for developing apps which will use the
zstd library

%package -n	%{devname}
Summary:	Header files for developing apps which will use zstd
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}

%description -n	%{devname}
Header files of zstd functions, for developing apps which
will use the zstd library.

%package -n	%{sdevname}
Summary:	Static libraries for zstd
Group:		Development/C
Requires:	%{devname} = %{version}-%{release}

%description -n	%{sdevname}
Static library for zstd

%prep
%setup -q
%apply_patches

%build
%make CC=%{__cc} CFLAGS="%{optflags} -std=c11" PREFIX="%{_prefix}" LIBDIR="%{_libdir}"

%install
%makeinstall_std PREFIX="%{_prefix}" LIBDIR="%{_libdir}"

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
