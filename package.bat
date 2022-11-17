mkdir osmpoly_export
mkdir osmpoly_export\icons
mkdir osmpoly_export\i18n
mkdir osmpoly_export\ui
xcopy *.py osmpoly_export
xcopy README.md osmpoly_export
xcopy LICENSE osmpoly_export
xcopy metadata.txt osmpoly_export
xcopy icons\osmpoly_export.png osmpoly_export\icons\
xcopy /F i18n\*.qm osmpoly_export\i18n
xcopy /F ui\* osmpoly_export\ui
zip -r osmpoly_export.zip osmpoly_export
del /Q osmpoly_export
rd osmpoly_export