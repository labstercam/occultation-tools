"""
Print help() for SharpCap APIs used by GOTO and Plate Solve flows.

Scope is intentionally limited to functions/properties relevant to:
- slew/goto
- plate solve
- mount status
- async control

Intended usage: run inside SharpCap's Python scripting environment,
where `sharpcap` is available.
"""
def _section(title):
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def _print_help(label, obj):
    _section(label)
    if obj is None:
        print("Not available")
        return

    try:
        help(obj)
    except Exception as ex:
        print("help() failed for {0}: {1}".format(label, ex))


def _print_value(label, value):
    _section(label)
    try:
        print(value)
    except Exception as ex:
        print("Could not read value for {0}: {1}".format(label, ex))


def _safe_getattr(obj, name):
    try:
        return getattr(obj, name)
    except Exception:
        return None


def print_relevant_sharpcap_help(sharpcap, coordinate_parser=None, plate_solve_purpose=None):
    """Print help() for only the relevant APIs used in main_gui.py GOTO/Plate Solve flow."""
    if sharpcap is None:
        print("No sharpcap object supplied.")
        return

    # Core app-level async APIs
    _print_help("sharpcap.SafeWaitForAsync", _safe_getattr(sharpcap, "SafeWaitForAsync"))
    _print_help("sharpcap.SafeGetAsyncResult", _safe_getattr(sharpcap, "SafeGetAsyncResult"))

    # Coordinate parsing used before StartSlewToAsync
    if coordinate_parser is not None:
        _print_help("CoordinateParser.Parse", _safe_getattr(coordinate_parser, "Parse"))
    else:
        print("\nCoordinateParser instance not provided; skipping CoordinateParser.Parse help.")

    # Mount APIs used by GOTO
    mounts = _safe_getattr(sharpcap, "Mounts")
    _print_help("sharpcap.Mounts", mounts)

    selected_mount = _safe_getattr(mounts, "SelectedMount") if mounts is not None else None
    _print_help("sharpcap.Mounts.SelectedMount", selected_mount)

    if selected_mount is not None:
        _print_help("mount.StartSlewToAsync", _safe_getattr(selected_mount, "StartSlewToAsync"))
        _print_help("mount.WaitUntilSettled", _safe_getattr(selected_mount, "WaitUntilSettled"))
        _print_help("mount.SolveAndSync", _safe_getattr(selected_mount, "SolveAndSync"))
        _print_help("mount.Slewing", _safe_getattr(selected_mount, "Slewing"))
        _print_help("mount.IsSettled", _safe_getattr(selected_mount, "IsSettled"))

        # Advanced diagnostics useful for GOTO/plate solve reliability and coordinate frame checks
        _print_help("mount.Coordinates", _safe_getattr(selected_mount, "Coordinates"))
        _print_help("mount.TargetPosition", _safe_getattr(selected_mount, "TargetPosition"))
        _print_help("mount.WouldGOTOChangeSideOfPier", _safe_getattr(selected_mount, "WouldGOTOChangeSideOfPier"))
        _print_help("mount.Epoch", _safe_getattr(selected_mount, "Epoch"))
        _print_help("mount.IsJNow", _safe_getattr(selected_mount, "IsJNow"))
        _print_help("mount.SiderealTime", _safe_getattr(selected_mount, "SiderealTime"))
        _print_help("mount.IsPlateSolveAvailable", _safe_getattr(selected_mount, "IsPlateSolveAvailable"))

        # Runtime values (not just type help), to confirm J2000/JNow behavior in-session
        _print_value("mount.Epoch (current value)", _safe_getattr(selected_mount, "Epoch"))
        _print_value("mount.IsJNow (current value)", _safe_getattr(selected_mount, "IsJNow"))
    else:
        print("\nNo selected mount; skipping mount-specific help sections.")

    # Plate solve APIs
    blind_solver = _safe_getattr(sharpcap, "BlindSolver")
    _print_help("sharpcap.BlindSolver", blind_solver)
    _print_help("BlindSolver.IsAvailable", _safe_getattr(blind_solver, "IsAvailable"))
    _print_help("BlindSolver.SolveAsync", _safe_getattr(blind_solver, "SolveAsync"))
    _print_help("BlindSolver.SolveExAsync", _safe_getattr(blind_solver, "SolveExAsync"))

    if plate_solve_purpose is not None:
        _print_help("plate_solve_purpose.Annotation", _safe_getattr(plate_solve_purpose, "Annotation"))
    else:
        print("\nplate_solve_purpose not provided; skipping Annotation member help.")

    # Cancellation token used in async calls
    try:
        threading_module = __import__("System.Threading", fromlist=["CancellationToken"])
        CancellationToken = getattr(threading_module, "CancellationToken", None)
        _print_help("System.Threading.CancellationToken", CancellationToken)
    except Exception as ex:
        print("\nCould not import CancellationToken: {0}".format(ex))


def main():
    # SharpCap script host usually exposes root-level SharpCap.
    # Keep compatibility with older/lowercase variants too.
    sc = (
        globals().get("SharpCap", None)
        or globals().get("sharpcap", None)
        or locals().get("SharpCap", None)
        or locals().get("sharpcap", None)
    )

    # Coordinate parser may be provided either as an instance or as a type.
    coord_parser = (
        globals().get("CoordinateParser", None)
        or locals().get("CoordinateParser", None)
    )

    # PlateSolvePurpose may be available as type/enum in script context.
    ps_purpose = (
        globals().get("PlateSolvePurpose", None)
        or locals().get("PlateSolvePurpose", None)
    )

    if sc is None:
        print("No SharpCap object found. Expected root-level 'SharpCap' in script context.")
        print("If needed, call print_relevant_sharpcap_help(SharpCap) explicitly.")
        return

    print_relevant_sharpcap_help(sc, coordinate_parser=coord_parser, plate_solve_purpose=ps_purpose)


if __name__ == "__main__":
    main()
