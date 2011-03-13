# package derived from:
# http://download.opensuse.org/repositories/home://dmacvicar:/gitorious/openSUSE_Factory/src/

%define	railsv	2.3.10
Name:		gitorious
Version:	0.9
Release:	%mkrel 5
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
Patch6:		gitorious-0.9-no-hard-version-dependency.patch
Patch7:		gitorious-0.9-use-aspell-en-dictionary-by-default.patch

Url:		http://www.gitorious.org/
Group:		Development/Other
Summary:	Web based code collaboration
BuildArch:	noarch

Requires:	rubygem(raspell)
Suggests:	aspell-en
Requires:	git
Requires:	git-core
Requires:	ImageMagick
Requires:	rubygem(BlueCloth)
Requires:	rubygem(archive-tar-minitar)
Requires:	rubygem(chronic)
Requires:	rubygem(diff-lcs)
Requires:	rubygem(echoe)
Requires:	rubygem(fastthread)
Requires:	rubygem(geoip)
Requires:	rubygem(highline)
Requires:	rubygem(json)
Requires:	rubygem(mime-types)
Requires:	rubygem(nokogiri)
Requires:	rubygem(oauth)
Requires:	rubygem(oniguruma)
Requires:	rubygem(rdiscount)
Requires:	rubygem(RedCloth)
Requires:	rubygem(ruby-hmac)
Requires:	rubygem(ruby-openid)
Requires:	rubygem(ruby-yadis)

Requires:	rubygem(stomp)
Requires:	rubygem(stompserver)

Requires:	apache-mpm-prefork
Requires:	rubygem(passenger)

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
Requires:	rubygem(mysql) mysql
Provides:	%{name}-database

%description	mysql
Meta package for %{name} mysql setup.

%package	postgresql
Summary:	Meta package for %{name} postgresql setup
Group:		Development/Other
Requires:	rubygem(postgres) postgresql-plpgsql
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
%patch6 -p1 -b .gemver~
%patch7 -p1 -b .aspell_en~
find -name .gitignore|xargs rm -f
# FIXME: hardcoding version is lame
sed -e "s#RAILS_GEM_VERSION = '.*'#RAILS_GEM_VERSION = '%{railsv}'#g" -i config/environment.rb
rm -rf vendor/rails vendor/oauth vendor/plugins/ultrasphinx

%build

%install
rm -rf %{buildroot}

# more crap
install -d %{buildroot}%{_var}/www/%{name}
cp -R Rakefile app bin config data db doc lib log public script test tmp vendor %{buildroot}%{_var}/www/%{name}
find %{buildroot} -name \*~ -delete

# add the init files
install -m755 %{SOURCE1} -D %{buildroot}%{_initrddir}/gitorious-git-daemon
install -m755 %{SOURCE2} -D %{buildroot}%{_initrddir}/gitorious-poller
install -m755 %{SOURCE3} -D %{buildroot}%{_initrddir}/gitorious-ultrasphinx

# make the gitorious client available in the path
install -d %{buildroot}%{_bindir}
ln -s %{_var}/www/%{name}/script/gitorious %{buildroot}%{_bindir}/gitorious

install -m644 %{SOURCE4} -D %{buildroot}%{_sysconfdir}/sysconfig/gitorious

# create the repositories directory
install -d -m755 %{buildroot}%{_localstatedir}/lib/git

# configure the instance
cat > %{buildroot}%{_var}/www/%{name}/config/gitorious.yml <<EOF
production:
  cookie_secret:
  repository_base_path: "%{_localstatedir}/lib/git"
  extra_html_head_data:
  system_message:
  gitorious_client_port: 3000
  gitorious_client_host: localhost.localdomain
  gitorious_host: localhost.localdomain
  gitorious_user: git
  exception_notification_emails:
  mangle_email_addresses: false
  public_mode: true
  locale: en
  archive_cache_dir: "%{_var}/cache/%{name}/tarballs"
  archive_work_dir: "%{_var}/tmp/%{name}/tarballs"
  only_site_admins_can_create_projects: false
  hide_http_clone_urls: false
  is_gitorious_dot_org: false
EOF

cat > %{buildroot}%{_var}/www/%{name}/config/broker.yml <<EOF
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
  XSendFilePath %{_var}/cache/%{name}/tarballs
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

touch %{buildroot}%{_var}/www/%{name}/config/database.yml
install -d %{buildroot}%{_var}/{run,log}/%{name}
install -d %{buildroot}%{_var}/{cache,tmp}/%{name}/tarballs

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
%dir %{_var}/cache/%{name}
%dir %{_var}/cache/%{name}/tarballs
%dir %{_var}/tmp/%{name}
%dir %{_var}/tmp/%{name}/tarballs
%dir %{_var}/run/%{name}
%dir %{_var}/log/%{name}
%dir %{_var}/www/%{name}
%{_var}/www/%{name}/Rakefile
%{_var}/www/%{name}/app/
%{_var}/www/%{name}/bin/
%dir %{_var}/www/%{name}/config
%config(noreplace) %{_var}/www/%{name}/config/broker.yml
%ghost %config(noreplace) %{_var}/www/%{name}/config/database.yml
%config(noreplace) %{_var}/www/%{name}/config/gitorious.yml
%config(noreplace) %{_var}/www/%{name}/config/jsTestDriver.conf
%{_var}/www/%{name}/config/broker.yml.example
%{_var}/www/%{name}/config/database.sample.yml
%{_var}/www/%{name}/config/gitorious.sample.yml
%{_var}/www/%{name}/config/*.rb
%{_var}/www/%{name}/config/environments
%{_var}/www/%{name}/config/initializers
%{_var}/www/%{name}/config/locales
%{_var}/www/%{name}/config/ultrasphinx
%{_var}/www/%{name}/data/
%{_var}/www/%{name}/db/
%{_var}/www/%{name}/doc/
%{_var}/www/%{name}/lib/
%{_var}/www/%{name}/log/
%{_var}/www/%{name}/public/
%{_var}/www/%{name}/script/
%{_var}/www/%{name}/test/
%{_var}/www/%{name}/tmp/
%{_var}/www/%{name}/vendor/

%files mysql
%files postgresql
