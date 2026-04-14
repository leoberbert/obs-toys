from __future__ import annotations

import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk, Pango  # noqa: E402

from .catalog import load_catalog
from .installer import install_plugin, remove_plugin
from .models import PluginRecipe
from .obs import close_obs, is_obs_installed, is_obs_running, plugin_status


ICON_PATH = Path(__file__).resolve().parent / "data" / "icons" / "obs-toys.svg"
GITHUB_ICON_PATH = Path(__file__).resolve().parent / "data" / "icons" / "github.svg"
GITHUB_LIGHT_ICON_PATH = Path(__file__).resolve().parent / "data" / "icons" / "github-light.svg"


class PluginCard(Gtk.Button):
    def __init__(self, recipe: PluginRecipe, on_activate) -> None:
        super().__init__()
        self.recipe = recipe
        self._on_activate = on_activate

        self.add_css_class("card")
        self.add_css_class("flat")
        self.set_can_focus(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)
        self.connect("clicked", self._handle_click)

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        content.set_margin_top(8)
        content.set_margin_bottom(8)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_size_request(168, 58)

        left_pad = Gtk.Label()
        left_pad.set_size_request(10, 1)

        title = Gtk.Label(label=recipe.name)
        title.add_css_class("heading")
        title.set_wrap(True)
        title.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        title.set_justify(Gtk.Justification.CENTER)
        title.set_halign(Gtk.Align.CENTER)
        title.set_valign(Gtk.Align.CENTER)
        title.set_max_width_chars(20)
        title.set_width_chars(4)
        title.set_hexpand(True)

        self._state_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
        self._state_icon.set_pixel_size(24)
        self._state_icon.set_halign(Gtk.Align.END)
        self._state_icon.set_valign(Gtk.Align.CENTER)

        content.append(left_pad)
        content.append(title)
        content.append(self._state_icon)

        self.set_child(content)

    def _handle_click(self, _button: Gtk.Button) -> None:
        self._on_activate(self.recipe)

    def matches_query(self, query: str) -> bool:
        haystack = (
            f"{self.recipe.name} {self.recipe.summary} "
            f"{self.recipe.description} {self.recipe.plugin_id}"
        ).lower()
        return query in haystack

    def set_installed(self, installed: bool) -> None:
        icon_name = "list-remove-symbolic" if installed else "list-add-symbolic"
        self._state_icon.set_from_icon_name(icon_name)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application) -> None:
        super().__init__(application=application, title="OBS Toys")
        self.set_default_size(800, 580)

        self._recipes = load_catalog()
        self._cards: list[PluginCard] = []
        self._selected_recipe: PluginRecipe | None = None
        self._project_icons: list[Gtk.Image] = []
        self._style_manager = Adw.StyleManager.get_default()
        self._style_manager.connect("notify::dark", self._on_theme_changed)

        self._header_bar = Adw.HeaderBar()
        self._back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self._back_button.set_tooltip_text("Back")
        self._back_button.set_visible(False)
        self._back_button.connect("clicked", self._show_catalog_page)
        self._header_bar.pack_start(self._back_button)

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search plugins")
        self._search_entry.set_size_request(250, -1)
        self._search_entry.connect("search-changed", self._on_search_changed)
        self._header_bar.pack_start(self._search_entry)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(self._header_bar)

        self._status_banner = Adw.Banner()
        self._status_banner.set_title("OBS system profile not detected.")
        self._status_banner.set_button_label("Refresh")
        self._status_banner.connect("button-clicked", lambda *_args: self._refresh_environment())

        self._main_stack = Gtk.Stack()
        self._main_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self._main_stack.set_transition_duration(0)
        self._main_stack.add_named(self._build_catalog_page(), "catalog")
        self._main_stack.add_named(self._build_detail_page(), "detail")

        toolbar.set_content(self._main_stack)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        container.append(self._status_banner)
        container.append(toolbar)
        self.set_content(container)

        self._populate_catalog()
        self._show_catalog_page()
        self._refresh_environment()

    def _build_catalog_page(self) -> Gtk.Widget:
        intro_group = Adw.PreferencesGroup()

        intro_row = Adw.ActionRow()
        intro_row.set_title("Welcome to OBS Toys")
        intro_row.set_subtitle("A friendly app for installing OBS plugins on Linux.")

        if ICON_PATH.exists():
            logo = Gtk.Image.new_from_file(str(ICON_PATH))
            logo.set_pixel_size(42)
            logo.set_valign(Gtk.Align.CENTER)
            intro_row.add_prefix(logo)

        project_button = self._create_project_button("https://github.com/leoberbert/obs-toys")
        project_button.set_valign(Gtk.Align.CENTER)
        intro_row.add_suffix(project_button)
        intro_group.add(intro_row)

        self._empty_state = Adw.StatusPage()
        self._empty_state.set_icon_name("system-search-symbolic")
        self._empty_state.set_title("No plugins found")
        self._empty_state.set_description("Try another search term to see more plugins.")
        self._empty_state.set_visible(False)

        self._catalog_flowbox = Gtk.FlowBox()
        self._catalog_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self._catalog_flowbox.set_valign(Gtk.Align.START)
        self._catalog_flowbox.set_hexpand(True)
        self._catalog_flowbox.set_vexpand(True)
        self._catalog_flowbox.set_max_children_per_line(5)
        self._catalog_flowbox.set_min_children_per_line(1)
        self._catalog_flowbox.set_homogeneous(True)
        self._catalog_flowbox.set_column_spacing(16)
        self._catalog_flowbox.set_row_spacing(12)
        self._catalog_flowbox.set_margin_top(8)
        self._catalog_flowbox.set_margin_bottom(32)
        self._catalog_flowbox.set_margin_start(32)
        self._catalog_flowbox.set_margin_end(32)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_vexpand(True)
        content.append(intro_group)
        content.append(self._empty_state)
        content.append(self._catalog_flowbox)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(content)
        return scroll

    def _build_detail_page(self) -> Gtk.Widget:
        self._detail_title = Gtk.Label(xalign=0)
        self._detail_title.add_css_class("title-1")
        self._detail_title.set_wrap(True)
        self._detail_title.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self._detail_title.set_halign(Gtk.Align.FILL)

        self._detail_summary = Gtk.Label(xalign=0)
        self._detail_summary.add_css_class("dim-label")
        self._detail_summary.set_wrap(True)
        self._detail_summary.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self._detail_summary.set_halign(Gtk.Align.FILL)

        self._detail_description = Gtk.TextView()
        self._detail_description.set_editable(False)
        self._detail_description.set_cursor_visible(False)
        self._detail_description.set_can_focus(False)
        self._detail_description.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._detail_description.set_left_margin(0)
        self._detail_description.set_right_margin(0)
        self._detail_description.set_top_margin(6)
        self._detail_description.set_bottom_margin(6)
        self._detail_description.set_vexpand(False)
        self._detail_description.set_hexpand(True)
        self._detail_description.set_size_request(-1, 110)
        self._detail_description.add_css_class("view")

        self._status_row = Adw.ActionRow(title="Status")
        self._location_row = Adw.ActionRow(title="Location")

        details_group = Adw.PreferencesGroup(title="Plugin Details")
        details_group.add(self._status_row)
        details_group.add(self._location_row)

        self._install_button = Gtk.Button(label="Install Plugin")
        self._install_button.add_css_class("suggested-action")
        self._install_button.connect("clicked", self._install_selected_plugin)

        self._remove_button = Gtk.Button(label="Remove Plugin")
        self._remove_button.add_css_class("destructive-action")
        self._remove_button.connect("clicked", self._remove_selected_plugin)

        self._project_button = self._create_project_button()

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions.set_halign(Gtk.Align.START)
        actions.append(self._install_button)
        actions.append(self._remove_button)
        actions.append(self._project_button)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.append(self._detail_title)
        content.append(self._detail_summary)
        content.append(self._detail_description)
        content.append(details_group)
        content.append(actions)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(700)
        clamp.set_child(content)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page.set_hexpand(True)
        page.set_vexpand(True)
        page.append(clamp)
        return page

    def _create_project_button(self, uri: str = "") -> Gtk.LinkButton:
        button = Gtk.LinkButton(uri=uri, label="")
        button.set_tooltip_text("Project Page")
        icon_path = self._current_github_icon_path()
        if icon_path.exists():
            icon = Gtk.Image.new_from_file(str(icon_path))
            icon.set_pixel_size(22)
            button.set_child(icon)
            self._project_icons.append(icon)
        else:
            button.set_label("GitHub")
        return button

    def _current_github_icon_path(self) -> Path:
        if self._style_manager.get_dark() and GITHUB_LIGHT_ICON_PATH.exists():
            return GITHUB_LIGHT_ICON_PATH
        return GITHUB_ICON_PATH

    def _on_theme_changed(self, _style_manager: Adw.StyleManager, _param_spec: object) -> None:
        icon_path = self._current_github_icon_path()
        if not icon_path.exists():
            return
        for icon in self._project_icons:
            icon.set_from_file(str(icon_path))

    def _populate_catalog(self) -> None:
        for recipe in self._recipes:
            card = PluginCard(recipe, self._show_plugin_page)
            self._cards.append(card)
            self._catalog_flowbox.append(card)

    def _show_catalog_page(self, *_args) -> None:
        self._selected_recipe = None
        self._back_button.set_visible(False)
        self._main_stack.set_visible_child_name("catalog")

    def _show_plugin_page(self, recipe: PluginRecipe) -> None:
        self._selected_recipe = recipe
        self._detail_title.set_label(recipe.name)
        self._detail_summary.set_label(recipe.summary)
        self._detail_description.get_buffer().set_text(recipe.description)
        self._project_button.set_uri(recipe.project_url)
        self._update_status(recipe)
        self._back_button.set_visible(True)
        self._main_stack.set_visible_child_name("detail")
        self._back_button.grab_focus()

    def _on_search_changed(self, _entry: Gtk.SearchEntry) -> None:
        query = self._search_entry.get_text().strip().lower()
        visible_count = 0

        for card in self._cards:
            visible = not query or card.matches_query(query)
            card.set_visible(visible)
            if visible:
                visible_count += 1

        self._empty_state.set_visible(visible_count == 0)

        if not query and self._main_stack.get_visible_child_name() != "detail":
            self._show_catalog_page()

    def _refresh_environment(self) -> None:
        installed = is_obs_installed()
        self._status_banner.set_revealed(not installed)

        for card in self._cards:
            card.set_installed(plugin_status(card.recipe).installed)

        if self._selected_recipe is not None:
            self._update_status(self._selected_recipe)

    def _update_status(self, recipe: PluginRecipe) -> None:
        status = plugin_status(recipe)
        self._status_row.set_subtitle("Installed" if status.installed else "Not installed")
        self._location_row.set_subtitle(str(status.plugin_path))
        self._install_button.set_visible(not status.installed)
        self._install_button.set_sensitive(is_obs_installed())
        self._remove_button.set_visible(status.installed)
        self._remove_button.set_sensitive(status.installed)
        for card in self._cards:
            if card.recipe.plugin_id == recipe.plugin_id:
                card.set_installed(status.installed)
                break

    def _install_selected_plugin(self, _button: Gtk.Button) -> None:
        if self._selected_recipe is None:
            return

        recipe = self._selected_recipe
        if is_obs_running():
            dialog = Adw.MessageDialog.new(
                self,
                "OBS is currently open",
                "Please close OBS before installing plugins. OBS Toys can try to close it for you and continue the installation.",
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("close_and_install", "Close OBS and Install")
            dialog.set_response_appearance("close_and_install", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("close_and_install")
            dialog.set_close_response("cancel")
            dialog.connect("response", self._on_close_obs_install_response, recipe)
            dialog.present()
            return

        self._present_install_confirmation(recipe)

    def _on_close_obs_install_response(
        self,
        dialog: Adw.MessageDialog,
        response: str,
        recipe: PluginRecipe,
    ) -> None:
        dialog.close()
        if response != "close_and_install":
            return

        if not close_obs():
            self._show_result_dialog(
                "Could Not Close OBS",
                "OBS Toys could not close OBS automatically. Please close it manually and try again.",
            )
            return

        self._present_install_confirmation(recipe)

    def _present_install_confirmation(self, recipe: PluginRecipe) -> None:
        dialog = Adw.MessageDialog.new(
            self,
            f"Install {recipe.name}?",
            "This will download the plugin release and copy its files into your OBS system profile.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install Plugin")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("install")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_install_response, recipe)
        dialog.present()

    def _on_install_response(
        self,
        dialog: Adw.MessageDialog,
        response: str,
        recipe: PluginRecipe,
    ) -> None:
        dialog.close()
        if response != "install":
            return

        self._install_button.set_sensitive(False)
        self._remove_button.set_sensitive(False)

        def worker() -> None:
            result = install_plugin(recipe)

            def finish() -> None:
                self._update_status(recipe)
                self._show_result_dialog(
                    "Plugin Installed" if result.success else "Installation Failed",
                    result.message,
                )

            GLib.idle_add(finish)

        threading.Thread(target=worker, daemon=True).start()

    def _remove_selected_plugin(self, _button: Gtk.Button) -> None:
        if self._selected_recipe is None:
            return

        recipe = self._selected_recipe
        dialog = Adw.MessageDialog.new(
            self,
            f"Remove {recipe.name}?",
            "This will remove the plugin files from your OBS system profile.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove", "Remove Plugin")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_remove_response, recipe)
        dialog.present()

    def _on_remove_response(
        self,
        dialog: Adw.MessageDialog,
        response: str,
        recipe: PluginRecipe,
    ) -> None:
        dialog.close()
        if response != "remove":
            return

        self._install_button.set_sensitive(False)
        self._remove_button.set_sensitive(False)

        def worker() -> None:
            result = remove_plugin(recipe)

            def finish() -> None:
                self._update_status(recipe)
                self._show_result_dialog(
                    "Plugin Removed" if result.success else "Removal Failed",
                    result.message,
                )

            GLib.idle_add(finish)

        threading.Thread(target=worker, daemon=True).start()

    def _show_result_dialog(self, title: str, body: str) -> None:
        dialog = Adw.MessageDialog.new(self, title, body)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.connect("response", lambda dlg, _response: dlg.close())
        dialog.present()
