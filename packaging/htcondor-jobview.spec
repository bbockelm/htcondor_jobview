Name:		htcondor-jobview
Version:	0.1
Release:	1%{?dist}
Summary:	A simple monitoring page for HTCondor sites

Group:		Applications/Internet
License:	ASL 2.0
URL:		https://github.com/bbockelm/htcondor_jobview

BuildArch:	noarch 

#
# To generate a new tarball, run the following from the source directory:
# python setup.py sdist
# cp dist/htcondor-jobview-*.tar.gz ~/rpmbuild/SOURCES
#
Source0:	%{name}-%{version}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	python-genshi
Requires:	python-genshi
Requires:	mod_wsgi
Requires:	httpd

%description
%{summary}


%prep
%setup -q


%build
python setup.py build


%install
rm -rf %{buildroot}
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES


%clean
rm -rf $RPM_BUILD_ROOT


%files -f INSTALLED_FILES
%config(noreplace) %_sysconfdir/jobview.conf
%config(noreplace) %_sysconfdir/httpd/conf.d/htcondor-jobview.conf
%defattr(-,root,root)


%changelog
* Fri Feb 15 2013 Brian Bockelman <bbockelm@cse.unl.edu> - 0.1-1
- Initial packaging of jobview prototype.


