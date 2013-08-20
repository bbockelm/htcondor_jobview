Name:		htcondor-jobview
Version:	0.5
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

# Github source0
# https://github.com/bbockelm/htcondor_jobview/archive/v0.4.tar.gz
Source0:	https://github.com/bbockelm/htcondor_jobview/archive/v%{version}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	python-genshi
Requires:	python-genshi
Requires:	mod_wsgi
Requires:	httpd
Requires:       rrdtool-python

%description
%{summary}


%prep
%setup -q


%build
python setup.py build


%install
rm -rf %{buildroot}
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
mkdir -p $RPM_BUILD_ROOT/var/lib/jobview

%clean
rm -rf $RPM_BUILD_ROOT


%files -f INSTALLED_FILES
%defattr(-,root,root)
%config(noreplace) %_sysconfdir/jobview.conf
%config(noreplace) %_sysconfdir/httpd/conf.d/htcondor-jobview.conf
%verify(not group user) %config(noreplace) %_sysconfdir/cron.d/jobview.cron
%attr(0755,apache,apache) %dir /var/lib/jobview


%changelog
* Mon Aug 19 2013 Derek Weitzel <dweitzel@cse.unl.edu> - 0.5-1
- Updating to v0.5

* Wed Feb 21 2013 Brian Bockelman <bbockelm@cse.unl.edu> - 0.4-1
- Create graphs for various schedd stats

* Wed Feb 20 2013 Brian Bockelman <bbockelm@cse.unl.edu> - 0.3-1
- Create RRD graphs.
- Allow webpage to auto-reload.
- Finish missing tables.  Port of old framework complete.

* Fri Feb 15 2013 Brian Bockelman <bbockelm@cse.unl.edu> - 0.1-1
- Initial packaging of jobview prototype.


