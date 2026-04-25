"""Dialog for renaming observation files to match the generated report name."""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

import os
import re

from System.Drawing import Point, Size, Font, FontStyle, Color
from System.Windows.Forms import (
    Form, Button, Label, GroupBox, CheckBox, TextBox,
    DialogResult, FormStartPosition, FormBorderStyle,
    MessageBox, MessageBoxButtons, MessageBoxIcon,
)

_SCAN_EXTENSIONS = (
    '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif', '.lc',
)


class RenameFilesDialog(Form):
    """Dialog to rename observation files to match the report name stem.

    Shows two sections:
      1. Selected observation files (light curve CSV, AOTA XML, AOTA report) passed in.
      2. Image files discovered in the observation folder.

    All files are checked by default.  On confirmation each checked file is
    renamed so its stem matches ``report_stem`` while its extension is preserved.
    Files whose target name already exists are skipped and reported.
    """

    def __init__(self, report_path, observation_folder, selected_files,
                 theme_manager=None):
        """
        Args:
            report_path:        Full path to the generated report file.
            observation_folder: Folder to scan for image files.  May be None.
            selected_files:     List of absolute paths to observation files that
                                were used as inputs (CSV, AOTA XML, AOTA report).
                                Only paths that actually exist are shown.
            theme_manager:      Optional theme manager for styling.
        """
        Form.__init__(self)

        self._report_stem = os.path.splitext(os.path.basename(report_path))[0]
        self._observation_folder = observation_folder
        self._theme_manager = theme_manager

        # Keep only files that actually exist on disk
        self._selected_files = [
            p for p in (selected_files or []) if p and os.path.isfile(p)
        ]

        # Discover image files in the observation folder (case-insensitive dedup,
        # excluding any paths already in _selected_files)
        _selected_lower = set(p.lower() for p in self._selected_files)
        self._image_files = []
        if observation_folder and os.path.isdir(observation_folder):
            seen = set()
            try:
                for fname in os.listdir(observation_folder):
                    if fname.lower().endswith(_SCAN_EXTENSIONS):
                        full = os.path.join(observation_folder, fname)
                        key = full.lower()
                        if key not in seen and key not in _selected_lower:
                            seen.add(key)
                            self._image_files.append(full)
            except Exception:
                pass
            self._image_files.sort()

        # (CheckBox, file_path, TextBox) triples populated by _setup_ui
        self._checkboxes = []
        self._btn_rename = None  # set in _setup_ui; used by _update_rename_button

        self._setup_ui()

        if theme_manager:
            try:
                from theme import apply_theme_to_control
                apply_theme_to_control(self, theme_manager.get_current_theme())
            except Exception:
                pass

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.Text = "Rename Files to Match Report"
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.StartPosition = FormStartPosition.CenterParent

        PAD_L = 14
        INNER_W = 760
        y = 14

        # ── Instruction ──────────────────────────────────────────────
        lbl_instr = Label()
        lbl_instr.Text = (
            "Proposed new names are shown on the right — edit them if needed before renaming:"
        )
        lbl_instr.Location = Point(PAD_L, y)
        lbl_instr.Size = Size(INNER_W, 18)
        self.Controls.Add(lbl_instr)
        y += 22

        # ── Report name (bold) ────────────────────────────────────────
        lbl_name = Label()
        lbl_name.Text = self._report_stem
        lbl_name.Location = Point(PAD_L, y)
        lbl_name.Size = Size(INNER_W, 18)
        lbl_name.AutoEllipsis = True
        try:
            lbl_name.Font = Font(
                lbl_name.Font.FontFamily,
                lbl_name.Font.Size,
                FontStyle.Bold,
            )
            lbl_name.ForeColor = Color.DarkBlue
        except Exception:
            pass
        self.Controls.Add(lbl_name)
        y += 28

        # ── Selected observation files ────────────────────────────────
        if self._selected_files:
            grp_obs = GroupBox()
            grp_obs.Text = "Selected Observation Files"
            grp_obs.Location = Point(PAD_L, y)
            grp_obs.Width = INNER_W
            inner_y = 20
            self._add_column_headers(grp_obs, inner_y, INNER_W)
            inner_y += 22
            for fpath in self._selected_files:
                self._make_row(fpath, grp_obs, inner_y, INNER_W)
                inner_y += 30
            grp_obs.Height = inner_y + 8
            self.Controls.Add(grp_obs)
            y += grp_obs.Height + 8

        # ── Image files ───────────────────────────────────────────────
        if self._image_files:
            grp_img = GroupBox()
            grp_img.Text = "Image and Light Curve Files in Observation Folder"
            grp_img.Location = Point(PAD_L, y)
            grp_img.Width = INNER_W
            inner_y = 20
            self._add_column_headers(grp_img, inner_y, INNER_W)
            inner_y += 22
            for fpath in self._image_files:
                self._make_row(fpath, grp_img, inner_y, INNER_W)
                inner_y += 30
            grp_img.Height = inner_y + 8
            self.Controls.Add(grp_img)
            y += grp_img.Height + 8

        # ── Nothing found ─────────────────────────────────────────────
        if not self._selected_files and not self._image_files:
            lbl_none = Label()
            lbl_none.Text = "No observation files found to rename."
            lbl_none.Location = Point(PAD_L, y)
            lbl_none.AutoSize = True
            self.Controls.Add(lbl_none)
            y += 30

        y += 10

        # ── Buttons ───────────────────────────────────────────────────
        btn_rename = Button()
        btn_rename.Text = "Rename Selected Files"
        btn_rename.AutoSize = True
        btn_rename.Location = Point(PAD_L, y)
        btn_rename.Enabled = bool(self._checkboxes)
        btn_rename.Click += self._on_rename_click
        self.Controls.Add(btn_rename)
        self._btn_rename = btn_rename

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.AutoSize = True
        btn_cancel.DialogResult = DialogResult.Cancel
        self.CancelButton = btn_cancel
        self.Controls.Add(btn_cancel)

        def _layout(s, e):
            btn_cancel.Location = Point(btn_rename.Right + 8, btn_rename.Top)
            self.ClientSize = Size(
                self.ClientSize.Width, btn_rename.Bottom + 16
            )

        self.Layout += _layout
        self.ClientSize = Size(INNER_W + 2 * PAD_L, y + 50)

    @staticmethod
    def _build_target_stem(src_fname, report_stem):
        """Return the target filename stem for *src_fname*.

        Preserves:
        * ``_AOTA_*`` suffix  (e.g. ``_AOTA_Xcorr``)
        * ``_Bin{N}`` tag that appears before ``_AOTA`` (e.g. ``_Bin1``)

        Examples::

            12_22_12_AOTA_Xcorr.png      ->  <report>_AOTA_Xcorr
            12_11_22_Bin1_AOTA_Xcorr.png ->  <report>_Bin1_AOTA_Xcorr
            12_11_22_plain.csv           ->  <report>
        """
        # Strip extension(s)
        if src_fname.lower().endswith('.aota.xml'):
            stem = src_fname[:-len('.aota.xml')]
        else:
            stem = os.path.splitext(src_fname)[0]

        aota_idx = stem.lower().find('_aota')
        if aota_idx < 0:
            return report_stem

        aota_suffix = stem[aota_idx:]    # e.g. _AOTA_Xcorr
        before_aota = stem[:aota_idx]    # e.g. 12_11_22_Bin1

        bin_match = re.search(r'_[Bb]in\d+', before_aota)
        bin_suffix = bin_match.group(0) if bin_match else ''

        return report_stem + bin_suffix + aota_suffix

    def _add_column_headers(self, parent, inner_y, group_width):
        """Add 'Current filename' / 'New filename' column header labels."""
        LBL_X = 30
        LBL_W = 280
        ARR_X = LBL_X + LBL_W + 6
        TXT_X = ARR_X + 24

        lbl_h1 = Label()
        lbl_h1.Text = "Current filename"
        lbl_h1.Location = Point(LBL_X, inner_y)
        lbl_h1.Size = Size(LBL_W, 16)
        try:
            lbl_h1.Font = Font(lbl_h1.Font.FontFamily, lbl_h1.Font.Size, FontStyle.Bold)
        except Exception:
            pass
        parent.Controls.Add(lbl_h1)

        lbl_h2 = Label()
        lbl_h2.Text = "New filename (editable)"
        lbl_h2.Location = Point(TXT_X, inner_y)
        lbl_h2.Size = Size(group_width - TXT_X - 12, 16)
        try:
            lbl_h2.Font = Font(lbl_h2.Font.FontFamily, lbl_h2.Font.Size, FontStyle.Bold)
        except Exception:
            pass
        parent.Controls.Add(lbl_h2)

    def _make_row(self, fpath, parent, inner_y, group_width):
        """Create a row: checkbox + original name label + arrow + editable new-name TextBox."""
        LBL_X = 30
        LBL_W = 280
        ARR_X = LBL_X + LBL_W + 6
        TXT_X = ARR_X + 24
        TXT_W = group_width - TXT_X - 16

        cb = CheckBox()
        cb.Text = ""
        cb.Checked = True
        cb.Location = Point(8, inner_y + 4)
        cb.Size = Size(18, 18)
        cb.Tag = fpath
        parent.Controls.Add(cb)

        lbl = Label()
        lbl.Text = os.path.basename(fpath)
        lbl.Location = Point(LBL_X, inner_y + 6)
        lbl.Size = Size(LBL_W, 18)
        lbl.AutoEllipsis = True
        parent.Controls.Add(lbl)

        lbl_arr = Label()
        lbl_arr.Text = "\u2192"
        lbl_arr.Location = Point(ARR_X, inner_y + 6)
        lbl_arr.Size = Size(20, 18)
        parent.Controls.Add(lbl_arr)

        fname = os.path.basename(fpath)
        if fname.lower().endswith('.aota.xml'):
            src_ext = '.aota.xml'
        else:
            src_ext = os.path.splitext(fname)[1]
        proposed = self._build_target_stem(fname, self._report_stem) + src_ext

        txt = TextBox()
        txt.Text = proposed
        txt.Location = Point(TXT_X, inner_y + 3)
        txt.Size = Size(TXT_W, 22)
        parent.Controls.Add(txt)

        def _on_check(s, e, t=txt, _self=self):
            t.Enabled = s.Checked
            _self._update_rename_button()

        cb.CheckedChanged += _on_check
        self._checkboxes.append((cb, fpath, txt))

    def _update_rename_button(self):
        """Enable Rename button only when at least one checkbox is checked."""
        if self._btn_rename is not None:
            self._btn_rename.Enabled = any(
                cb.Checked for cb, _, _t in self._checkboxes
            )

    # ------------------------------------------------------------------
    # Rename logic
    # ------------------------------------------------------------------

    def _on_rename_click(self, sender, e):
        """Compute renames, detect conflicts, execute, report results."""
        conflicts = []
        rename_pairs = []

        for cb, src_path, txt in self._checkboxes:
            if not cb.Checked:
                continue

            new_name = txt.Text.strip()
            if not new_name:
                continue
            new_path = os.path.join(os.path.dirname(src_path), new_name)

            # Already the correct name — nothing to do
            if os.path.normcase(src_path) == os.path.normcase(new_path):
                continue

            if os.path.exists(new_path):
                conflicts.append(os.path.basename(new_path))
            else:
                rename_pairs.append((src_path, new_path))

        # Report conflicts before attempting any renames
        if conflicts:
            conflict_list = "\n".join("  \u2022  " + c for c in conflicts)
            MessageBox.Show(
                "The following target names already exist and will NOT be renamed:\n\n"
                + conflict_list,
                "File Conflicts",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning,
            )

        if not rename_pairs:
            if not conflicts:
                # Nothing was checked or all names already match
                MessageBox.Show(
                    "No files need renaming — all selected names already match.",
                    "Nothing to Rename",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information,
                )
            # Conflicts were already reported; leave dialog open so user can edit names
            return

        errors = []
        for src, dst in rename_pairs:
            try:
                os.rename(src, dst)
            except Exception as ex:
                errors.append("{0}: {1}".format(os.path.basename(src), ex))

        renamed_count = len(rename_pairs) - len(errors)
        if errors:
            MessageBox.Show(
                "Some files could not be renamed:\n\n" + "\n".join(errors),
                "Rename Errors",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error,
            )
        if renamed_count > 0 and not errors:
            # Show success only when no errors; error messagebox already drew attention
            skipped_note = (
                "\n({0} skipped due to conflicts)".format(len(conflicts))
                if conflicts else ""
            )
            MessageBox.Show(
                "Renamed {0} file(s) successfully.{1}".format(renamed_count, skipped_note),
                "Rename Complete",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information,
            )

        self.DialogResult = DialogResult.OK
        self.Close()
