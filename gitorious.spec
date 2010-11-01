# package derived from:
# http://download.opensuse.org/repositories/home://dmacvicar:/gitorious/openSUSE_Factory/src/

%define	railsv	2.3.10
Name:		gitorious
Version:	0.9
Release:	%mkrel 1
License:	AGPLv3
# 2ba975497d9d1fa0014d0414631210726c7ef0f3
Source0:	gitorious.tar.xz
Source1:	gitorious-git-daemon.init
Source2:	gitorious-poller.init
Source3:	gitorious-ultrasphinx.init
Source4:	sysconfig.gitorious
Source5:	gitorious-setup-1st-time
Patch0:		gitorious-0.9-ultrasphinx-conf-template.patch
Patch2:		gitorious-0.9-relative_url_root.patch
Patch3:		gitorious-0.9-poller-pid-path.patch
Patch4:		gitorious-0.9-use-system-oauth-gem.patch
Patch5:		gitorious-0.9-ruby-shellbang-path-fix.patch

Url:		http://www.gitorious.org/
Group:		Development/Other
Summary:	Web based code collaboration
BuildArch:	noarch

Requires:	aspell
Suggests:	aspell-en
Requires:	git
Requires:	git-core
Requires:	ImageMagick
Requires:	ruby-mysql
Requires:	rubygem-BlueCloth
Requires:	rubygem-archive-tar-minitar
Requires:	rubygem(chronic)
Requires:	ruby-diff-lcs
Requires:	rubygem(echoe)
Requires:	rubygem-fastthread
Requires:	ruby-geoip
Requires:	rubygem-highline
Requires:	rubygem-json
Requires:	rubygem-mime-types
Requires:	rubygem-nokogiri
Requires:	rubygem-oauth
Requires:	rubygem-oniguruma
Requires:	ruby-rdiscount
Requires:	rubygem-RedCloth
Requires:	rubygem-ruby-hmac
Requires:	rubygem-ruby-openid
Requires:	rubygem-ruby-yadis

Requires:	ruby-stomp
Requires:	rubygem(stompserver)

Requires:	apache-mpm-prefork
Requires:	rubygem-passenger

Requires:	memcached
Requires:	sendmail-command
# Required for source tarball download to work
Requires:	apache-mod_xsendfile
Requires:	apache-mod_ssl
Requires:	%{name}-database

Requires:	rubygem(ultrasphinx)
Requires:	sphinx
BuildRequires:	sphinx

Requires:	rubygem(rails) = %{railsv}
BuildRequires:	rubygem(rails) = %{railsv}
# we need hostname to configure, and dd for generating random string
BuildRequires:	net-tools coreutils gawk
# required by rpm build to check symbols in JsTestDriver-1.0b.jar
BuildRequires:	fastjar

BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
Gitorious aims to provide a great way of doing distributed opensource code collaboration.

%package	mysql
Summary:	Meta package for %{name} mysql setup
Group:		Development/Other
Requires:	ruby-mysql mysql
Provides:	%{name}-database

%description	mysql
Meta package for %{name} mysql setup.

%package	postgresql
Summary:	Meta package for %{name} postgresql setup
Group:		Development/Other
Requires:	ruby-postgres postgresql-plpgsql
Provides:	%{name}-database

%description	postgresql
Meta package for %{name} postgresql setup.

%prep
%setup -q -n gitorious
cp config/ultrasphinx/{default,production}.base
%patch0 -p0 -b .ultrasphinx_production~
%patch2 -p1 -b .url_root~
%patch3 -p1 -b .pidpath~
%patch4 -p1 -b .oauth_gem~
%patch5 -p1 -b .shellbang~
find -name .gitignore|xargs rm -f
# FIXME: hardcoding version is lame
sed -e "s#RAILS_GEM_VERSION = '.*'#RAILS_GEM_VERSION = '%{railsv}'#g" -i config/environment.rb
rm -rf vendor/rails vendor/oauth vendor/plugins/ultrasphinx

%build

%install
rm -rf %{buildroot}

# more crap
install -d %{buildroot}%{_var}/www/gitorious
cp -R Rakefile app bin config data db doc lib log public script test tmp vendor %{buildroot}%{_var}/www/gitorious
find %{buildroot} -name \*~ -delete

# add the init files
install -m755 %{SOURCE1} -D %{buildroot}%{_initrddir}/gitorious-git-daemon
install -m755 %{SOURCE2} -D %{buildroot}%{_initrddir}/gitorious-poller
install -m755 %{SOURCE3} -D %{buildroot}%{_initrddir}/gitorious-ultrasphinx

# make the gitorious client available in the path
install -d %{buildroot}%{_bindir}
ln -s %{_var}/www/gitorious/script/gitorious %{buildroot}%{_bindir}/gitorious

install -m644 %{SOURCE4} -D %{buildroot}%{_sysconfdir}/sysconfig/gitorious

# create the repositories directory
install -d -m755 %{buildroot}%{_localstatedir}/lib/git

# configure the instance
cat > %{buildroot}%{_var}/www/gitorious/config/gitorious.yml <<EOF
production:
  cookie_secret:
  repository_base_path: "%{_localstatedir}/lib/git"
  extra_html_head_data:
  system_message:
  gitorious_client_port: 3000
  gitorious_client_host: localhost
  gitorious_host: localhost
  gitorious_user: git
  exception_notification_emails:
  mangle_email_addresses: false
  public_mode: true
  locale: en
  archive_cache_dir: "%{_var}/cache/gitorious/tarballs"
  archive_work_dir: "%{_var}/tmp/gitorious/tarballs"
  only_site_admins_can_create_projects: false
  hide_http_clone_urls: false
  is_gitorious_dot_org: false
EOF

cat > %{buildroot}%{_var}/www/gitorious/config/broker.yml <<EOF
production:
    adapter: stomp
EOF

# install the first time configuration tool
install -m755 %{SOURCE5} -D %{buildroot}%{_bindir}/gitorious-setup-1st-time

install -d %{buildroot}%{webappconfdir}
cat >>  %{buildroot}%{webappconfdir}/%{name}.conf <<EOF
# Enable X-SendFile for Gitorious repo archiving to work  
<IfModule mod_xsendfile.c>
  XSendFile on
  XSendFileAllowAbove on
</IfModule>

<IfModule mod_alias.c>
  Alias /%{name} %{_var}/www/%{name}/public
</IfModule>

<IfModule mod_passenger.c>
  <Directory "%{_var}/www/%{name}/public">
    Order allow,deny
    Allow from All

    PassengerAppRoot %{_var}/www/%{name}
  </Directory>
</IfModule>
EOF

touch %{buildroot}%{_var}/www/gitorious/config/database.yml
install -d %{buildroot}%{_var}/{run,log}/gitorious
install -d %{buildroot}%{_var}/{cache,tmp}/gitorious/tarballs

install -d %{buildroot}%{_localstatedir}/lib/git/.ssh
touch %{buildroot}%{_localstatedir}/lib/git/.ssh/authorized_keys

%clean
rm -rf %{buildroot}

%pre
%_pre_useradd git %{_localstatedir}/lib/git /bin/true

%post
%{_post_service gitorious-git-daemon}
%{_post_service gitorious-poller}
%{_post_service gitorious-ultrasphinx}

%preun
%{_preun_service gitorious-git-daemon}
%{_preun_service gitorious-poller}
%{_preun_service gitorious-ultrasphinx}

%postun
%_postun_userdel git

%files
%defattr(-,root,root)
%doc README HACKING AUTHORS TODO.txt
%{_bindir}/gitorious-setup-1st-time
%{_bindir}/gitorious
%{_initrddir}/gitorious-*
%config(noreplace) %{_sysconfdir}/sysconfig/gitorious
%config(noreplace) %{webappconfdir}/%{name}.conf
%defattr(-,git,root)
%dir %{_localstatedir}/lib/git
%attr(700,git,root) %dir %{_localstatedir}/lib/git/.ssh
%attr(600,git,root) %config(noreplace) %{_localstatedir}/lib/git/.ssh/authorized_keys
%dir %{_var}/cache/gitorious
%dir %{_var}/cache/gitorious/tarballs
%dir %{_var}/tmp/gitorious
%dir %{_var}/tmp/gitorious/tarballs
%dir %{_var}/run/gitorious
%dir %{_var}/log/gitorious
%dir %{_var}/www/gitorious
%{_var}/www/gitorious/Rakefile
%{_var}/www/gitorious/app/
%{_var}/www/gitorious/bin/
%dir %{_var}/www/gitorious/config
%config(noreplace) %{_var}/www/gitorious/config/broker.yml
%ghost %config(noreplace) %{_var}/www/gitorious/config/database.yml
%config(noreplace) %{_var}/www/gitorious/config/gitorious.yml
%config(noreplace) %{_var}/www/gitorious/config/jsTestDriver.conf
%{_var}/www/gitorious/config/broker.yml.example
%{_var}/www/gitorious/config/database.sample.yml
%{_var}/www/gitorious/config/gitorious.sample.yml
%{_var}/www/gitorious/config/*.rb
%{_var}/www/gitorious/config/environments
%{_var}/www/gitorious/config/initializers
%{_var}/www/gitorious/config/locales
%{_var}/www/gitorious/config/ultrasphinx
%{_var}/www/gitorious/data/
%{_var}/www/gitorious/db/
%{_var}/www/gitorious/doc/
%{_var}/www/gitorious/lib/
%{_var}/www/gitorious/log/
%{_var}/www/gitorious/public/
%{_var}/www/gitorious/script/
%{_var}/www/gitorious/test/
%{_var}/www/gitorious/tmp/
%{_var}/www/gitorious/vendor/

%files mysql
%files postgresql
