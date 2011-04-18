# This file is part of Palabra
#
# Copyright (C) 2009 - 2011 Simeon Visser
#
# Palabra is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import operator
import pangocairo

import constants

class Histogram:
    def __init__(self, totals, width, height):
        self.width = width
        self.height = height
        
        self.bar_spacing = 1
        minimum_height = 3
        maximum = max([value for key, value in totals])

        self.bars = []
        for i, (key, value) in enumerate(totals):
            try:
                ratio = value / float(maximum)
                available = (self.height - minimum_height)
                bar_item_height = int(ratio * available)
            except ZeroDivisionError:
                bar_item_height = 0
            
            bar_width = int(float(self.width) / len(totals))
            bar_height = minimum_height + bar_item_height
            
            bar = (key, value, bar_width, bar_height)
            self.bars.append(bar)
        
    def set_ordering(self, ordering):
        if ordering == constants.ORDERING_ALPHABET:
            self.bars.sort(key=operator.itemgetter(0))
        elif ordering == constants.ORDERING_FREQUENCY:
            self.bars.sort(key=operator.itemgetter(1), reverse=True)
        
    def draw(self, context):
        for i, (key, value, bar_width, bar_height) in enumerate(self.bars):
            x = i * (bar_width + self.bar_spacing)
            y = self.height - bar_height
            
            red = green = blue = 0
            if value == 0:
                red = 1
            else:
                red = 0
            context.set_source_rgb(red, green, blue)
            context.rectangle(x, y, bar_width, bar_height)
            context.fill()
            
            context.set_source_rgb(0, 0, 0)
            self.draw_key(context, key, x + bar_width / 4, self.height)
        
    def draw_key(self, context, key, x, y):
        xbearing, ybearing, width, height, xadvance, yadvance = context.text_extents(key)

        pcr = pangocairo.CairoContext(context)
        layout = pcr.create_layout()
        layout.set_markup('''<span font_desc="%s">%s</span>''' % ("Sans 10", key))
        
        context.save()
        context.move_to(x, y)
        pcr.show_layout(layout)
        context.restore()

class PropertiesWindow(gtk.Dialog):
    def __init__(self, palabra_window, puzzle):
        gtk.Dialog.__init__(self, u"Puzzle properties", palabra_window
            , gtk.DIALOG_MODAL)
        self.palabra_window = palabra_window
        self.puzzle = puzzle
        self.connect("destroy", lambda widget: self.palabra_window.editor.clear_highlighted_words())

        status = puzzle.grid.determine_status(True)
        message = self.determine_words_message(status, puzzle)
        
        tabs = gtk.Notebook()
        tabs.append_page(self.create_general_tab(status, puzzle), gtk.Label(u"General"))
        tabs.append_page(self.create_letters_tab(status, puzzle), gtk.Label(u"Letters"))
        tabs.append_page(self.create_words_tab(message, status, puzzle), gtk.Label(u"Words"))
        tabs.append_page(self.create_metadata_tab(puzzle), gtk.Label(u"Metadata"))
        tabs.append_page(self.create_notepad_tab(puzzle), gtk.Label(u"Notepad"))
        tabs.connect("switch-page", self.on_switch_page)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(tabs, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT)
        self.vbox.add(hbox)
        
    def on_switch_page(self, tabs, page, pagenum):
        self.words_tab_sel.unselect_all()
        self.palabra_window.editor.clear_highlighted_words()
    
    def create_general_tab(self, status, puzzle):
        table = gtk.Table(13, 4, False)
        table.set_col_spacings(18)
        table.set_row_spacings(6)
        
        def create_header(table, title, x, y):
            label = gtk.Label()
            label.set_markup(title)
            label.set_alignment(0, 0)
            table.attach(label, x, x + 1, y, y + 1)
            label = gtk.Label("")
            label.set_alignment(1, 0)
            table.attach(label, x + 1, x + 2, y, y + 1)
        def create_statistic(table, title, value, x, y):
            label = gtk.Label(title)
            label.set_alignment(0, 0)
            table.attach(label, x, x + 1, y, y + 1)
            label = gtk.Label(value)
            label.set_alignment(1, 0)
            table.attach(label, x + 1, x + 2, y, y + 1)
            
        create_header(table, u"<b>Grid</b>", 0, 0)
        create_statistic(table, u"Columns", str(puzzle.grid.width), 0, 1)
        create_statistic(table, u"Rows", str(puzzle.grid.height), 0, 2)
        
        create_header(table, u"<b>Cells</b>", 0, 3)
        msg = ''.join([str(status["block_count"]), u" (%.2f" % status["block_percentage"], u"%)"])
        create_statistic(table, u"Blocks", msg, 0, 4)
        msg = ''.join([str(status["actual_char_count"]), " / ", str(status["char_count"])])
        create_statistic(table, u"Letters", msg, 0, 5)
        create_statistic(table, u"Voids", str(status["void_count"]), 0, 6)
        create_statistic(table, u"Checked cells", str(status["checked_count"]), 0, 7)
        create_statistic(table, u"Unchecked cells", str(status["unchecked_count"]), 0, 8)
        create_statistic(table, u"Open cells", str(status["open_count"]), 0, 9)
        
        create_header(table, u"<b>Words</b>", 2, 0)
        create_statistic(table, u"Total words", str(status["word_count"]), 2, 1)
        create_statistic(table, u"Across words", str(status["word_counts"]["across"]), 2, 2)
        create_statistic(table, u"Down words", str(status["word_counts"]["down"]), 2, 3)
        message = u"%.2f" % status["mean_word_length"]
        create_statistic(table, u"Average word length", message, 2, 4)
        msg = ''.join([str(status["clue_count"]), " / ", str(status["word_count"])])
        create_statistic(table, u"Clues", msg, 2, 5)
        create_statistic(table, u"Connected?", "Yes" if status["connected"] else "No", 2, 6)
        
        create_header(table, u"<b>Score</b>", 2, 7)
        score = self.determine_scrabble_score(puzzle)
        create_statistic(table, u"Scrabble score", str(score), 2, 8)
        try:
            avg_score = float(score) / status["char_count"]
        except ZeroDivisionError:
            avg_score = 0
        create_statistic(table, u"Average letter score", "%.2f" % avg_score, 2, 9)
        
        create_header(table, u"<b>Letters</b>", 0, 10)
        
        letters_in_use = [c for (c, count) in status["char_counts_total"] if count > 0]
        letters_not_in_use = [c for (c, count) in status["char_counts_total"] if count == 0]
        
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        main.pack_start(table, False, False, 0)
        
        label = gtk.Label(u"Letters in use")
        label.set_alignment(0, 0)
        table.attach(label, 0, 1, 11, 12)
        msg = ''.join(letters_in_use) if letters_in_use else "(none)"
        label = gtk.Label(msg)
        label.set_alignment(0, 0)
        table.attach(label, 1, 4, 11, 12)
        
        label = gtk.Label(u"Letters not in use")
        label.set_alignment(0, 0)
        table.attach(label, 0, 1, 12, 13)
        msg = ''.join(letters_not_in_use) if letters_not_in_use else "(none, this is a pangram)"
        label = gtk.Label(msg)
        label.set_alignment(0, 0)
        table.attach(label, 1, 4, 12, 13)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, False, False, 0)
        return hbox
        
    def create_letters_tab(self, status, puzzle):
        table = gtk.Table(5, 6, False)
        table.set_col_spacings(18)
        table.set_row_spacings(6)
        
        self.histogram = Histogram(status["char_counts_total"], 312, 90)
        
        def on_char_click(widget, event, char):
            self.palabra_window.editor.highlight_chars(char)
        
        for y in xrange(0, 26, 6):
            for x, (char, count) in enumerate(status["char_counts_total"][y:y + 6]):
                if count == 0:
                    label = gtk.Label()
                    label.set_markup(''.join([char, u": <b>0</b>"]))
                else:
                    label = gtk.Label(''.join([char, u": ", str(count), u""]))
                eventbox = gtk.EventBox()
                eventbox.add(label)
                eventbox.connect("button-press-event", on_char_click, char)
                table.attach(eventbox, x, x + 1, y / 6, y / 6 + 1)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        label = gtk.Label(u"Click on a character to see occurrences in the puzzle:")
        label.set_alignment(0, 0.5)
        main.pack_start(label, False, False, 0)
        main.pack_start(table, False, False, 0)
        
        def on_expose_event(drawing_area, event):
            context = drawing_area.window.cairo_create()
            self.histogram.draw(context)
            return True
        
        combo = gtk.combo_box_new_text()
        combo.append_text(u"Alphabet")
        combo.append_text(u"Frequency")
        combo.set_active(0)
        combo.connect("changed", self.on_ordering_changed)
        
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.set_size_request(self.histogram.width, self.histogram.height)
        self.drawing_area.connect("expose_event", on_expose_event)
        
        histo_hbox = gtk.HBox(False, 0)
        histo_hbox.pack_start(self.drawing_area, True, True, 0)
        
        histo_options = gtk.VBox(False, 0)
        
        label = gtk.Label(u"Order by:")
        label.set_alignment(0, 0.5)
        histo_options.pack_start(label, False, False, 3)
        histo_options.pack_start(combo, False, False, 3)
        histo_hbox.pack_start(histo_options, False, False, 0)
        
        main.pack_start(histo_hbox, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox
        
    def on_ordering_changed(self, combo):
        if combo.get_active() == 0:
            self.histogram.set_ordering(constants.ORDERING_ALPHABET)
        elif combo.get_active() == 1:
            self.histogram.set_ordering(constants.ORDERING_FREQUENCY)
        self.drawing_area.queue_draw()
                
    def create_stats_tab(self, message):
        text = gtk.TextView()
        text.set_editable(False)        
        data = text.get_buffer()
        data.set_text(message)
        
        scrolled_window = gtk.ScrolledWindow(None, None)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(text)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(scrolled_window, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox
        
    def create_words_tab(self, message, status, puzzle):
        store = gtk.ListStore(int, int)
        tree = gtk.TreeView(store)
        self.words_tab_sel = tree.get_selection()
        self.words_tab_sel.connect("changed", self.on_selection_changed)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Length", cell, text=0)
        tree.append_column(column)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Count", cell, text=1)
        tree.append_column(column)
        
        for i in status["word_counts"]["total"]:
            store.append(i)
        
        window = gtk.ScrolledWindow(None, None)
        window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        window.add(tree)
        
        text = gtk.TextView()
        text.set_editable(False)        
        data = text.get_buffer()
        data.set_text(message)
        
        twindow = gtk.ScrolledWindow(None, None)
        twindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        twindow.add_with_viewport(text)
        
        label = gtk.Label()
        label.set_markup(u"<b>Words</b>")        
        label.set_alignment(0, 0.5)
        label.set_padding(3, 3)
        
        text_vbox = gtk.VBox(False, 0)
        text_vbox.set_spacing(6)
        text_vbox.pack_start(label, False, False, 0)
        text_vbox.pack_start(twindow, True, True, 0)
        
        label = gtk.Label()
        label.set_markup(u"<b>Lengths</b>")        
        label.set_alignment(0, 0.5)
        label.set_padding(3, 3)
        
        lengths_vbox = gtk.VBox(False, 0)
        lengths_vbox.set_spacing(6)
        lengths_vbox.pack_start(label, False, False, 0)
        lengths_vbox.pack_start(window, True, True, 0)
        
        hhbox = gtk.HBox(False, 0)
        hhbox.set_spacing(18)
        hhbox.pack_start(text_vbox, True, True, 0)
        hhbox.pack_start(lengths_vbox, True, True, 0)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(hhbox, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox
    
    def on_selection_changed(self, selection):
        store, it = selection.get_selected()
        if it:
            length = store.get_value(it, 0)
            self.palabra_window.editor.highlight_words(length)
            
    @staticmethod
    def determine_scrabble_score(puzzle):
        # http://en.wikipedia.org/wiki/Scrabble_letter_distributions#English
        scores = {'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2
            , 'H': 4, 'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1
            , 'O': 1, 'P': 3, 'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1
            , 'V': 4, 'W': 4, 'X': 8, 'Y': 4, 'Z': 10, '': 0}
        chars = [puzzle.grid.get_char(x, y) for x, y in puzzle.grid.cells()]
        return sum([scores[c] for c in chars])
        
    @staticmethod
    def determine_words_message(status, puzzle):
        entries = puzzle.grid.entries()
        entries.sort(key=len)
        result = []
        for word in entries:
            result += (word + u"\n")
        return ''.join(result[:-1])
        
    def create_metadata_tab(self, puzzle):
        details = gtk.Table(9, 2, False)
        
        def metadata_changed(widget, key):
            value = widget.get_text().strip()
            self.puzzle.metadata[key] = value
            if len(value) == 0:
                del self.puzzle.metadata[key]
        
        def create_metadata_entry(key, label, index):
            entry = gtk.Entry(512)
            entry.connect("changed", lambda w: metadata_changed(w, key))
            alignment = gtk.Alignment(0, 0.5, 0, 0)
            alignment.add(gtk.Label(label))
            details.attach(alignment, 0, 1, index, index + 1)
            details.attach(entry, 1, 2, index, index + 1)
            
            try:
                value = puzzle.metadata[key]
                entry.set_text(value)
            except KeyError:
                pass
            
        create_metadata_entry("title", u"Title", 0)
        create_metadata_entry("creator", u"Creator", 1)
        create_metadata_entry("contributor", u"Editor", 2)
        create_metadata_entry("rights", u"Rights", 3)
        #create_metadata_entry("description", u"Description", 4)
        create_metadata_entry("publisher", u"Publisher", 4)
        create_metadata_entry("date", u"Date", 5)
        #create_metadata_entry("identifier", u"Identifier", 7)
        #create_metadata_entry("language", u"Language", 8)

        align = gtk.Alignment(0, 0, 1, 0)
        align.add(details)
        
        hhbox = gtk.HBox(False, 0)
        hhbox.set_spacing(18)
        hhbox.pack_start(align, True, True, 0)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(hhbox, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox
        
    def create_notepad_tab(self, puzzle):
        label = gtk.Label(u"The above text will be stored with the puzzle.")
        textview = gtk.TextView()
        textview.set_wrap_mode(gtk.WRAP_WORD)
        def on_notepad_changed(buffer):
            start = buffer.get_start_iter()
            end = buffer.get_end_iter()
            puzzle.notepad = buffer.get_text(start, end)
        textview.get_buffer().set_text(puzzle.notepad)
        textview.get_buffer().connect("changed", on_notepad_changed)
        
        text_window = gtk.ScrolledWindow(None, None)
        text_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        text_window.add(textview)
        
        vbox = gtk.VBox(False, 0)
        vbox.set_spacing(6)
        vbox.pack_start(text_window, True, True, 0)
        vbox.pack_start(label, False, False, 0)
    
        hhbox = gtk.HBox(False, 0)
        hhbox.set_spacing(18)
        hhbox.pack_start(vbox, True, True, 0)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(hhbox, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox
