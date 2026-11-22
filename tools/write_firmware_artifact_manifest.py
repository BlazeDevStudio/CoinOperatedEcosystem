            raise ManifestError(
                f"refusing symlink or non-regular artifact file: {relative}"
            )
        if before.st_nlink != 1:
            raise ManifestError(f"refusing hard-linked artifact file: {relative}")

        descriptor = -1
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW,
                dir_fd=directory_descriptor,
            )
            after = os.fstat(descriptor)
            if (
                not stat.S_ISREG(after.st_mode)
                or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                or after.st_nlink != 1
            ):
                raise ManifestError(f"artifact identity changed while opening: {relative}")

            digest = hashlib.sha256()
            total = 0
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                total += len(chunk)
            if total != after.st_size:
                raise ManifestError(f"artifact size changed while hashing: {relative}")

            # The pathname and inode can remain stable while another process
            # rewrites bytes in place. Compare a second descriptor snapshot
            # after the final read so a mixed/stale digest is never admitted.
            finished = os.fstat(descriptor)
            if (
                not stat.S_ISREG(finished.st_mode)
                or (after.st_dev, after.st_ino) != (finished.st_dev, finished.st_ino)
                or after.st_mode != finished.st_mode
                or after.st_nlink != finished.st_nlink
                or after.st_size != finished.st_size
                or after.st_mtime_ns != finished.st_mtime_ns
                or after.st_ctime_ns != finished.st_ctime_ns
            ):
                raise ManifestError(f"artifact file changed while hashing: {relative}")

            try:
                current = os.stat(
                    name,
                    dir_fd=directory_descriptor,
                    follow_symlinks=False,
                )
            except (OSError, TypeError, NotImplementedError) as exc:
                raise ManifestError(
                    f"artifact file changed while hashing: {relative}: {exc}"
                ) from exc
            if (
                not stat.S_ISREG(current.st_mode)
                or (finished.st_dev, finished.st_ino) != (current.st_dev, current.st_ino)
                or finished.st_mode != current.st_mode
                or finished.st_nlink != current.st_nlink
                or finished.st_size != current.st_size
                or finished.st_mtime_ns != current.st_mtime_ns
                or finished.st_ctime_ns != current.st_ctime_ns
            ):
                raise ManifestError(f"artifact file changed while hashing: {relative}")
        except (OSError, TypeError, NotImplementedError) as exc:
            raise ManifestError(f"could not safely hash artifact {relative}: {exc}") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)

        records.append(
            {
                "path": relative,
                "size": total,
                "sha256": digest.hexdigest(),
            }
        )


def _scan_artifact_files(
    artifact_dir: str,
    directory_descriptor: int | None = None,
) -> list[dict]:
    """Hash the artifact tree through pinned directory descriptors."""
    root = os.path.abspath(os.fspath(artifact_dir))
    _require_descriptor_scan_support()

    owns_descriptor = directory_descriptor is None
    if owns_descriptor:
        try:
            directory_descriptor = os.open(
                root,