# This file is part of Palabra
#
# Copyright (C) 2009 Simeon Visser
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
        self.puzzle = puzzle
        self.set_size_request(512, 512)
        
        details = gtk.Table(1, 2, False)
        
        title_hbox = gtk.HButtonBox()
        title_hbox.set_layout(gtk.BUTTONBOX_START)
        title_hbox.pack_start(gtk.Label("Title"), False, False, 0)
        title_entry = gtk.Entry(512)
        
        def title_changed(item):
            self.puzzle.metadata["title"] = item.get_text().strip()
        title_entry.connect("changed", title_changed)
        alignment = gtk.Alignment(0, 0.5, 0, 0)
        alignment.add(gtk.Label(u"Title"))
        details.attach(alignment, 0, 1, 0, 1)
        details.attach(title_entry, 1, 2, 0, 1)
        
        author_entry = gtk.Entry(512)
        
        def author_changed(item):
            self.puzzle.metadata["author"] = item.get_text().strip()
        author_entry.connect("changed", author_changed)
        alignment = gtk.Alignment(0, 0.5, 0, 0)
        alignment.add(gtk.Label(u"Author"))
        details.attach(alignment, 0, 1, 1, 2)
        details.attach(author_entry, 1, 2, 1, 2)
        
        copyright_hbox = gtk.HBox(False, 0)
        copyright_hbox.pack_start(gtk.Label(u"Copyright"), False, False, 0)
        copyright_entry = gtk.Entry(512)
        
        def copyright_changed(item):
            self.puzzle.metadata["copyright"] = item.get_text().strip()
        copyright_entry.connect("changed", copyright_changed)
        alignment = gtk.Alignment(0, 0.5, 0, 0)
        alignment.add(gtk.Label(u"Copyright"))
        details.attach(alignment, 0, 1, 2, 3)
        details.attach(copyright_entry, 1, 2, 2, 3)
        
        description_hbox = gtk.HBox(False, 0)
        description_hbox.pack_start(gtk.Label(u"Description"), False, False, 0)
        description_entry = gtk.Entry(512)
        
        def description_changed(item):
            self.puzzle.metadata["description"] = item.get_text().strip()
        description_entry.connect("changed", description_changed)
        alignment = gtk.Alignment(0, 0.5, 0, 0)
        alignment.add(gtk.Label(u"Description"))
        details.attach(alignment, 0, 1, 3, 4)
        details.attach(description_entry, 1, 2, 3, 4)

        if "title" in puzzle.metadata and puzzle.metadata["title"] is not None:
            title_entry.set_text(puzzle.metadata["title"])
        if "author" in puzzle.metadata and puzzle.metadata["author"] is not None:
            author_entry.set_text(puzzle.metadata["author"])
        if "copyright" in puzzle.metadata and puzzle.metadata["copyright"] is not None:
            copyright_entry.set_text(puzzle.metadata["copyright"])
        if "description" in puzzle.metadata and puzzle.metadata["description"] is not None:
            description_entry.set_text(puzzle.metadata["description"])
        
        status = puzzle.grid.determine_status(True)
        message = self.determine_words_message(status, puzzle)
        
        tabs = gtk.Notebook()
        tabs.append_page(self.create_general_tab(status, puzzle), gtk.Label(u"General"))
        tabs.append_page(self.create_letters_tab(status, puzzle), gtk.Label(u"Letters"))
        tabs.append_page(self.create_words_tab(message, status, puzzle), gtk.Label(u"Words"))
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(details, False, False, 0)
        main.pack_start(tabs, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT)
        self.vbox.add(hbox)
    
    def create_general_tab(self, status, puzzle):
        table = gtk.Table(8, 4, False)
        table.set_col_spacings(18)
        table.set_row_spacings(6)
        
        def create_statistic(table, title, value, x, y):
            label = gtk.Label(title)
            label.set_alignment(0, 0)
            table.attach(label, x, x + 1, y, y + 1)
            label = gtk.Label(value)
            label.set_alignment(1, 0)
            table.attach(label, x + 1, x + 2, y, y + 1)
            
        create_statistic(table, u"Columns", str(puzzle.grid.width), 0, 0)
        create_statistic(table, u"Rows", str(puzzle.grid.height), 0, 1)
        create_statistic(table, u"Blocks", str(status["block_count"]), 0, 2)
        message = ''.join([u"%.2f" % status["block_percentage"], u"%"])
        create_statistic(table, u"Block percentage", message, 0, 3)
        create_statistic(table, u"Letters", str(status["char_count"]), 0, 4)
        create_statistic(table, u"Clues", str(status["clue_count"]), 0, 5)
        
        create_statistic(table, u"Checked cells", str(status["checked_count"]), 2, 0)
        create_statistic(table, u"Unchecked cells", str(status["unchecked_count"]), 2, 1)
        create_statistic(table, u"Total words", str(status["word_count"]), 2, 2)
        create_statistic(table, u"Across words", str(status["across_word_count"]), 2, 3)
        create_statistic(table, u"Down words", str(status["down_word_count"]), 2, 4)
        message = u"%.2f" % status["mean_word_length"]
        create_statistic(table, u"Mean word length", message, 2, 5)
        
        letters_in_use = filter(lambda (_, count): count > 0, status["char_counts_total"])
        letters_in_use_strings = map(lambda (c, _): c, letters_in_use)
        
        letters_not_in_use = filter(lambda (_, count): count == 0, status["char_counts_total"])
        letters_not_in_use_strings = map(lambda (c, _): c, letters_not_in_use)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        main.pack_start(table, False, False, 0)
        
        label = gtk.Label(u"Letters in use")
        label.set_alignment(0, 0)
        table.attach(label, 0, 2, 6, 7)
        label = gtk.Label(''.join(letters_in_use_strings))
        label.set_alignment(0, 0)
        table.attach(label, 2, 4, 6, 7)
        
        label = gtk.Label(u"Letters not in use")
        label.set_alignment(0, 0)
        table.attach(label, 0, 2, 7, 8)
        label = gtk.Label(''.join(letters_not_in_use_strings))
        label.set_alignment(0, 0)
        table.attach(label, 2, 4, 7, 8)
        
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
        
        for y in xrange(0, 26, 6):
            for x, (char, count) in enumerate(status["char_counts_total"][y:y + 6]):
                if count == 0:
                    label = gtk.Label()
                    label.set_markup(''.join([char, u": <b>", str(count), u"</b>"]))
                else:
                    label = gtk.Label(''.join([char, u": ", str(count), u""]))
                table.attach(label, x, x + 1, y / 6, y / 6 + 1)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
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
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Length", cell, text=0)
        tree.append_column(column)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u"Count", cell, text=1)
        tree.append_column(column)
        
        for i in status["word_counts_total"]:
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
        
        hhbox = gtk.HBox(False, 0)
        hhbox.set_spacing(18)
        hhbox.pack_start(text_vbox, True, True, 0)
        hhbox.pack_start(window, True, True, 0)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(hhbox, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox
        
    @staticmethod
    def determine_words_message(status, puzzle):
        word_count_to_str = lambda (length, count): ''.join([str(length), u": ", str(count), u"\n"])
        
        a = [word for (n, x, y, word, clue, explanation) in puzzle.grid.gather_words("across")]
        d = [word for (n, x, y, word, clue, explanation) in puzzle.grid.gather_words("down")]
        words = (a + d)
        words.sort()
        words.sort(key=len)

        return ''.join(map(lambda word: ''.join([word, u"\n"]), words))
