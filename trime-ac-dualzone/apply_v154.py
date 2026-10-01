#!/usr/bin/env python3
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument("root", type=Path)
a = p.parse_args()
root = a.root


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) Fresh AC installs default to external sync again, and upgrades from the
# v1.5.3 APP_STORAGE default migrate exactly once.
app_prefs = root / "app/src/main/java/com/osfans/trime/data/prefs/AppPrefs.kt"
replace_once(
    app_prefs,
    '            const val USER_DB_MIGRATED = "profile_user_db_migrated"\n',
    '            const val USER_DB_MIGRATED = "profile_user_db_migrated"\n'
    '            const val AC_EXTERNAL_SYNC_V154_MIGRATED = "profile_ac_external_sync_v154_migrated"\n',
    "AppPrefs migration key",
)
replace_once(
    app_prefs,
    '        val dataStorageMode = enum(R.string.data_storage_mode, DATA_STORAGE_MODE, DataStorageMode.APP_STORAGE)\n',
    '        val dataStorageMode = enum(R.string.data_storage_mode, DATA_STORAGE_MODE, DataStorageMode.EXTERNAL_SYNC)\n',
    "AppPrefs external-sync default",
)
replace_once(
    app_prefs,
    '        val userDbMigrated = bool(USER_DB_MIGRATED, false)\n',
    '        val userDbMigrated = bool(USER_DB_MIGRATED, false)\n'
    '        val acExternalSyncV154Migrated = bool(AC_EXTERNAL_SYNC_V154_MIGRATED, false)\n',
    "AppPrefs migration delegate",
)

# 2) Dedicated /sdcard/AC-Trime root policy + one-time v1.5.3 migration.
sync = root / "app/src/main/java/com/osfans/trime/data/sync/RimeDataSync.kt"
replace_once(
    sync,
    'object RimeDataSync {\n    private val parallelism = Runtime.getRuntime().availableProcessors().coerceIn(4, 8)\n',
    'object RimeDataSync {\n'
    '    const val AC_EXTERNAL_DIR_NAME = "AC-Trime"\n'
    '    private const val EXTERNAL_STORAGE_AUTHORITY = "com.android.externalstorage.documents"\n\n'
    '    private val parallelism = Runtime.getRuntime().availableProcessors().coerceIn(4, 8)\n',
    "RimeDataSync dedicated-root constants",
)
replace_once(
    sync,
    '    fun treeUri(): Uri? = prefs.externalRimeTreeUri.getValue().takeIf { it.isNotEmpty() }?.let { Uri.parse(it) }\n\n',
    '    fun treeUri(): Uri? = prefs.externalRimeTreeUri.getValue().takeIf { it.isNotEmpty() }?.let { Uri.parse(it) }\n\n'
    '    fun acExternalInitialUri(): Uri =\n'
    '        DocumentsContract.buildDocumentUri(\n'
    '            EXTERNAL_STORAGE_AUTHORITY,\n'
    '            "primary:$AC_EXTERNAL_DIR_NAME",\n'
    '        )\n\n'
    '    fun isAcExternalTree(uri: Uri): Boolean =\n'
    '        runCatching {\n'
    '            val documentId = DocumentsContract.getTreeDocumentId(uri).trimEnd(\'/\')\n'
    '            val relative = documentId.substringAfter(\':\', documentId)\n'
    '            relative.substringAfterLast(\'/\') == AC_EXTERNAL_DIR_NAME\n'
    '        }.getOrDefault(false)\n\n'
    '    fun ensureAcExternalSyncV154Default() {\n'
    '        val profile = AppPrefs.defaultInstance().profile\n'
    '        if (profile.acExternalSyncV154Migrated.getValue()) return\n'
    '        if (profile.externalRimeTreeUri.getValue().isEmpty() &&\n'
    '            profile.dataStorageMode.getValue() == DataStorageMode.APP_STORAGE\n'
    '        ) {\n'
    '            profile.dataStorageMode.setValue(DataStorageMode.EXTERNAL_SYNC)\n'
    '        }\n'
    '        profile.acExternalSyncV154Migrated.setValue(true)\n'
    '    }\n\n',
    "RimeDataSync dedicated-root helpers",
)

# 3) Setup picker starts at AC-Trime, rejects broad roots, persists the SAF
# grant before import, and never revokes a successful grant because import failed.
setup = root / "app/src/main/java/com/osfans/trime/ui/setup/SetupActivity.kt"
old_picker = '''    private val dataPathPicker =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri == null) return@registerForActivityResult
            lifecycleScope.launch {
                runCatching {
                    withContext(Dispatchers.IO) {
                        RimeDataSync.persistTreeUri(this@SetupActivity, uri)
                        RimeDataSync.importToLocal(this@SetupActivity).getOrThrow()
                    }
                    refreshCurrentFragment()
                    updateButtons()
                    toast(R.string.setup__data_path_imported)
                    skipButton.visibility = View.VISIBLE
                }.onFailure {
                    withContext(Dispatchers.IO) {
                        RimeDataSync.clearExternalTree(this@SetupActivity)
                    }
                    refreshCurrentFragment()
                    updateButtons()
                    toast(R.string.setup__data_path_import_failed)
                }
            }
        }

    fun launchDataPathPicker() {
        dataPathPicker.launch(null as Uri?)
    }
'''
new_picker = '''    private val dataPathPicker =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri == null) return@registerForActivityResult
            if (!RimeDataSync.isAcExternalTree(uri)) {
                toast("请选择 /sdcard/${RimeDataSync.AC_EXTERNAL_DIR_NAME} 目录")
                return@registerForActivityResult
            }
            lifecycleScope.launch {
                runCatching {
                    withContext(Dispatchers.IO) {
                        // Persist the successful SAF grant first. Import failure must never
                        // make the directory look unselected again.
                        RimeDataSync.persistTreeUri(this@SetupActivity, uri)
                        RimeDataSync.importToLocal(this@SetupActivity).getOrThrow()
                    }
                    refreshCurrentFragment()
                    updateButtons()
                    toast(R.string.setup__data_path_imported)
                    skipButton.visibility = View.VISIBLE
                }.onFailure {
                    // Keep the persisted AC-Trime grant. The user can retry sync later
                    // without selecting the directory a second time.
                    refreshCurrentFragment()
                    updateButtons()
                    toast(R.string.setup__data_path_import_failed)
                }
            }
        }

    fun launchDataPathPicker() {
        dataPathPicker.launch(RimeDataSync.acExternalInitialUri())
    }
'''
replace_once(setup, old_picker, new_picker, "SetupActivity picker/import flow")
replace_once(
    setup,
    '        super.onCreate(savedInstanceState)\n        enableEdgeToEdge()\n',
    '        super.onCreate(savedInstanceState)\n        RimeDataSync.ensureAcExternalSyncV154Default()\n        enableEdgeToEdge()\n',
    "SetupActivity v1.5.4 migration",
)

print("V154_EXTERNAL_SYNC_DEFAULT_APPLIED")
print("V154_AC_TRIME_DEDICATED_ROOT_APPLIED")
print("V154_IMPORT_FAILURE_PRESERVES_SAF_GRANT")
print("V154_V153_STORAGE_MIGRATION_APPLIED")
