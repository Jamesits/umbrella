import logging
import os
import stat
import shutil
import pathlib
import typing
import sqlite3
import git
from .utils import url_hide_sensitive, get_timestamp, get_os_string

UMBRELLA_CORE_VERSION: int = 1
logger: logging.Logger = logging.getLogger(__name__)


class GitMirroredRepo:
    askpass_py_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'askpass.py')

    def __init__(
            self: 'GitMirroredRepo',
            storage_directory: typing.AnyStr,
            upstream_url: typing.Union[typing.AnyStr, None],

            git_username: typing.Union[typing.AnyStr, None] = None,
            git_password: typing.Union[typing.AnyStr, None] = None,
            git_ssh_key_path: typing.Union[typing.AnyStr, None] = None,

            git_lfs_enable: bool = True,
    ) -> None:
        self.storage_directory: str = str(storage_directory)
        self.upstream_url: typing.Union[str, None] = str(upstream_url) if upstream_url is not None else None
        self.repo: typing.Union[git.Repo, None] = None
        self.git_lfs_enabled: bool = git_lfs_enable

        self.git_username = git_username
        self.git_environment: typing.Dict[str, str] = dict()

        if git_username is not None:
            if git_password is not None:
                # https://stackoverflow.com/questions/44784828/gitpython-git-authentication-using-user-and-password
                self.git_environment['GIT_ASKPASS'] = str(self.askpass_py_path)
                self.git_environment['GIT_USERNAME'] = str(git_username)
                self.git_environment['GIT_PASSWORD'] = str(git_password)
            elif git_ssh_key_path is not None:
                # https://stackoverflow.com/questions/52592918/gitpython-cloning-with-ssh-key-host-key-verification-failed
                assert os.path.exists(git_ssh_key_path)
                self.git_environment['GIT_SSH_COMMAND'] = f"ssh -i '{git_ssh_key_path}'"

        self.git_directory: str = os.path.join(self.storage_directory, "git")
        self.umbrella_directory: str = os.path.join(self.storage_directory, "umbrella")
        self.temp_directory: str = os.path.join(self.storage_directory, "temp")
        self.initialized_file: str = os.path.join(self.umbrella_directory, "initialized")

        self.sqlite3_db_file: str = os.path.join(self.umbrella_directory, "umbrella.sqlite3")
        self.db_connection: sqlite3.Connection
        self.db_cursor: sqlite3.Cursor

        self.__init_dir()
        self.__init_db()

    def __init_db(self) -> None:
        """
        Initialize SQLite3 database for storing references. Always run after __init_dir()
        :return:
        """
        logger.info("Initializing database connection...")
        self.db_connection = sqlite3.connect(self.sqlite3_db_file)
        self.db_cursor = self.db_connection.cursor()

        self.db_cursor.execute(r"""CREATE TABLE IF NOT EXISTS "umbrella_config" (
            	"key"	TEXT,
                "value"	TEXT,
                PRIMARY KEY("key")
        );""")

        self.db_cursor.execute(r"""CREATE TABLE IF NOT EXISTS "objects_sha1" (
                "sha1"	BLOB,
                "type"  TEXT,
                "size"  INTEGER,
                "first_appearance_in_snapshots"	INTEGER,
                PRIMARY KEY("sha1")
        );""")

        self.db_cursor.execute(r"""CREATE TABLE IF NOT EXISTS "snapshots" (
                "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                "timestamp"	INTEGER,
                "umbrella_core_version"	INTEGER,
                "os"	TEXT
        );""")

        self.db_cursor.execute(r"""CREATE TABLE IF NOT EXISTS "configs" (
                "snapshot_id"	INTEGER PRIMARY KEY,
                "content"	BLOB
        );""")

        # the id=0 record denotes the information when the database is initialized
        # it is not a real snapshot
        self.db_cursor.execute(r"""
            INSERT OR IGNORE INTO "snapshots" ("id", "timestamp", "umbrella_core_version", "os") VALUES (?, ?, ?, ?);
        """, (0, get_timestamp(), UMBRELLA_CORE_VERSION, get_os_string()))

        self.db_connection.commit()

    def __db_get_current_snapshot_id(self) -> int:
        """
        Get the current snapshot id (self increment) after inserting a new snapshot entry.
        :return: an integer id
        """
        self.db_cursor.execute(r"""
            SELECT SEQ from sqlite_sequence WHERE name='snapshots';
        """)

        try:
            return int(self.db_cursor.fetchone()[0])
        except TypeError:
            return 0

    def __init_dir(self) -> None:
        """
        Set up directory structure.
        :return: None
        """
        os.makedirs(self.storage_directory, exist_ok=True)
        os.makedirs(self.umbrella_directory, exist_ok=True)

        if os.path.isfile(self.initialized_file):
            # the repo is initialized, read info from it
            logger.info(f"Reading Git repo at {self.git_directory}...")
            self.repo = git.Repo(self.git_directory)
            assert self.repo
            assert self.repo.remote("origin").exists()
            if self.upstream_url is None:
                self.upstream_url = self.repo.remote("origin").url
            else:
                assert self.upstream_url == self.repo.remote("origin").url
        else:
            logger.info(f"Initializing Git repo at {self.git_directory}...")
            # if a previous attempt failed, we have to remove the dead
            if os.path.exists(self.git_directory):
                shutil.rmtree(self.git_directory)
            # init repo
            self.repo = git.Repo.init(self.git_directory, bare=True)

            # not using repo.config_writer
            # In py3 __del__ calls can be delayed, thus not writing changes in time.
            # https://gitpython.readthedocs.io/en/stable/tutorial.html#meet-the-repo-type

            # add a remote
            # http://git.661346.n2.nabble.com/PATCH-1-2-clone-Add-an-option-to-set-up-a-mirror-td664305.html
            self.repo.create_remote("origin", self.upstream_url, mirror="fetch")
            # no auto CRLF conversion
            # https://stackoverflow.com/questions/21822650/disable-git-eol-conversions
            self.repo.git.config('core.autocrlf', 'false')
            # add the mirror config on the origin remote
            # (don't know what it affects really, but it is nice to mimic `git clone --mirror`)
            # https://stackoverflow.com/a/39266284/2646069
            self.repo.git.config('remote.origin.mirror', 'true')
            # disable GC to prevent Git deleting objects
            # https://stackoverflow.com/questions/28092485/how-to-prevent-garbage-collection-in-git
            self.repo.git.config('gc.auto', '0')
            self.repo.git.config('gc.pruneExpire', 'never')
            self.repo.git.config('gc.reflogExpire', 'never')
            self.repo.git.config('gc.autodetach', 'false')
            # disable interactive login
            # https://microsoft.github.io/Git-Credential-Manager-for-Windows/Docs/Configuration.html
            self.repo.git.config('credential.modalPrompt', 'false')
            # still allow login by saved credentials, e.g. Windows account
            self.repo.git.config('credential.authority', 'Auto')
            self.repo.git.config('credential.interactive', 'never')

        # completed
        pathlib.Path(self.initialized_file).touch(exist_ok=True)

        assert self.repo.bare

    def __unpack_git_objects(self) -> None:
        """
        Unpack all git packs into objects
        :return: None
        """
        shutil.rmtree(self.temp_directory, ignore_errors=True)
        os.makedirs(self.temp_directory, exist_ok=True)

        # unpack all the packs
        # https://stackoverflow.com/questions/16972031/how-to-unpack-all-objects-of-a-git-repository
        packs_dir = os.path.join(self.git_directory, "objects", "pack")
        pack_count = 0
        for pack_file in os.listdir(packs_dir):
            src = os.path.join(packs_dir, pack_file)
            os.chmod(src, stat.S_IREAD or stat.S_IWRITE)
            shutil.move(src, self.temp_directory)
        for f in os.listdir(self.temp_directory):
            file_full_path = os.path.join(self.temp_directory, f)
            if os.path.splitext(f)[-1] == ".pack":
                logger.info(f"Unpacking {f}...")
                with open(file_full_path, 'rb') as f_stream:
                    self.repo.git.unpack_objects("-r", "--strict", istream=f_stream)
                pack_count += 1
            os.chmod(file_full_path, stat.S_IREAD or stat.S_IWRITE)
            os.remove(file_full_path)

        shutil.rmtree(self.temp_directory, ignore_errors=True)

    def update(self) -> None:
        """
        Pull everything from the remote once. May throw git.exc.GitCommandError if failed.
        :return: None
        """
        assert self.repo
        assert self.repo.remote("origin").exists()
        assert self.upstream_url == self.repo.remote('origin').url

        if self.git_username is not None:
            self.repo.git.config('credential.username', self.git_username)
        else:
            try:
                self.repo.git.config('--unset', 'credential.username')
            except git.exc.GitCommandError:
                # might fail if the config does not exist in the first place
                pass

        # Update the mirror
        # https://stackoverflow.com/a/6151419/2646069
        logger.info(f"Fetching changes from {url_hide_sensitive(self.upstream_url)}...")
        self.repo.remote("origin").update(env=self.git_environment)

        # GitPython have no direct support for Git LFS: https://github.com/gitpython-developers/GitPython/issues/739
        # https://help.github.com/en/github/creating-cloning-and-archiving-repositories/duplicating-a-repository
        logger.info(f"Fetching LFS objects from {url_hide_sensitive(self.upstream_url)}...")
        self.repo.git.lfs('fetch', '--all')

    @staticmethod
    def __sha1_string_from_bytes(sha1: bytes) -> str:
        """
        Get the string hex form of the sha1 bytes object.
        :param sha1: The bytes object
        :return: the string form, e.g. "00e6ccf5da05d75c2c21068333ebfb920e4d6d3b"
        """
        return sha1.hex().rjust(40, '0')

    def __get_git_object_type(self, sha1: bytes) -> str:
        """
        Get the object type.
        Note: git cat-file is very slow
        :param sha1: the bytes object of the sha1
        :return: "tree" || "blob" || "commit" || "tag"
        """
        return str(self.repo.git.cat_file("-t", "--allow-unknown-type", self.__sha1_string_from_bytes(sha1)))

    def __get_git_object_size(self, sha1: bytes) -> int:
        """
        Get the object size in bytes.
        Note: git cat-file is very slow
        :param sha1: the bytes object of the sha1
        :return: object size in bytes
        """
        return int(self.repo.git.cat_file("-s", "--allow-unknown-type", self.__sha1_string_from_bytes(sha1)))

    def __db_fill_object_details(self) -> None:
        """
        Prefetch the object type and size into database. Note the object sha1 itself must be in the database first.
        Caution: very slow
        :return: None
        """
        self.db_cursor.execute(r"""
            SELECT "sha1", "type", "size" FROM "objects_sha1" WHERE "type" IS NULL OR "size" IS NULL;
        """)

        updated_rows = []
        object_count = 0
        for row in self.db_cursor:
            object_count += 1
            if object_count % 100 == 0:
                logger.info(f"Calculating object: {object_count}")
            sha1, t, s = row
            if t is None:
                t = self.__get_git_object_type(sha1)
            if s is None:
                s = self.__get_git_object_size(sha1)
            updated_rows.append((t, s, sha1))

        logger.info("Writing object metadata...")
        self.db_cursor.executemany("""UPDATE "objects_sha1" 
            SET "type" = ?, "size" = ?
            WHERE "sha1" = ?;
        """, updated_rows)
        self.db_connection.commit()
        logger.info(f"{object_count} objects documented.")

    def snapshot(self) -> None:
        """
        Log the repo status into the database
        :return: None
        """
        self.__unpack_git_objects()

        # create a new snapshot
        self.db_cursor.execute(r"""
                        INSERT INTO "snapshots" ("timestamp", "umbrella_core_version", "os") VALUES (?, ?, ?);
                    """, (get_timestamp(), UMBRELLA_CORE_VERSION, get_os_string()))
        snapshot_id: int = self.__db_get_current_snapshot_id()
        ref_table_name: str = f"refs_snapshot_{snapshot_id}"

        self.db_cursor.execute(fr"""CREATE TABLE IF NOT EXISTS "{ref_table_name}" (
                "path"	TEXT,
                "commit"	TEXT,
                PRIMARY KEY("path")
        );""")

        # save heads
        head: git.Reference
        head_count = 0
        for head in self.repo.references:
            # all we need is head path and commit (although annotated tags looks different in packed refs)
            # https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery
            # print(head.path, head.commit)
            self.db_cursor.execute(fr"""
                        INSERT INTO "{ref_table_name}" ("path", "commit") VALUES (?, ?);
                    """, (str(head.path), str(head.commit)))
            head_count += 1
        logger.info(f"{head_count} references saved.")

        # save config
        with open(os.path.join(self.git_directory, "config"), "r") as f:
            self.db_cursor.execute(r"""
                INSERT INTO "configs" ("snapshot_id", "content") VALUES (?, ?);
            """, (snapshot_id, f.read()))

        # save objects
        object_count = 0
        new_object_count = 0
        for sha1_hash in self.repo.odb.sha_iter():
            object_count += 1
            # if object_count % 100 == 0:
            #     logger.info(f"Scanning object: {object_count}")
            try:
                self.db_cursor.execute(r"""
                    INSERT INTO "objects_sha1" ("sha1", "first_appearance_in_snapshots") VALUES (?, ?);
                """, (sha1_hash, snapshot_id))
                new_object_count += 1
            except sqlite3.IntegrityError:
                pass

        logger.info(f"{new_object_count}/{object_count} new objects saved.")

        # commit
        self.db_connection.commit()

    def submodules(self):
        return [x.url for x in self.repo.submodules]
