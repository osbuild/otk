%global forgeurl https://github.com/osbuild/otk

Version:        2024.0.0
%forgemeta

Name:           otk
Release:        1
License:        Apache-2.0
URL:            %{forgeurl}
Source0:        %{forgesource}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-wheel
BuildRequires:  pyproject-rpm-macros


Summary: The omnifest toolkit

%generate_buildrequires
%pyproject_buildrequires

%description
The omnifest toolkit is a YAML transpiler to take omnifest inputs and
translate them into osbuild manifests.

%prep
%forgeautosetup

%build
%pyproject_wheel

%install
%pyproject_install

# Install the examples
mkdir -p %{buildroot}%{_datadir}/otk/example/
cp -a example/* %{buildroot}%{_datadir}/otk/example/


%files
%license LICENSE
%doc doc
%{_datadir}/otk
%{_bindir}/otk
%{_bindir}/osbuild-gen-depsolve-dnf4
%{_bindir}/osbuild-make-depsolve-dnf4-curl-source
%{_bindir}/osbuild-make-depsolve-dnf4-rpm-stage
%{_bindir}/osbuild-get-dnf4-package-info
%{python3_sitelib}/otk
%{python3_sitelib}/otk_external_osbuild
%{python3_sitelib}/otk-%{version}.dist-info


%changelog
* Wed May 08 2024 Brian C. Lane <bcl@redhat.com> - 2024.0.0-1
- Initial package creation
