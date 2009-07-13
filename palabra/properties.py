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
import pangocairo

class Histogram:
    def __init__(self, totals, width, height):
        self.totals = totals
        self.width = width
        self.height = height
        
        maximum = max([value for key, value in totals])
        
        self.bar_width = 15
        self.minimum_height = 3
        
        self.bars = []
        for key, value in totals:
            try:
                ratio = value / float(maximum)
                available = (self.height - self.minimum_height)
                bar_item_height = int(ratio * available)
            except ZeroDivisionError:
                bar_item_height = 0
            
            width = self.bar_width
            height = self.minimum_height + bar_item_height
            self.bars.append((key, width, height))
        
    def draw(self, context):
        for i, (key, width, height) in enumerate(self.bars):
            x = i * (self.bar_width + 1)
            y = self.height - height
            
            red = green = blue = 0
            if height == self.minimum_height:
                red = 1
            else:
                red = 0
            context.set_source_rgb(red, green, blue)
            context.rectangle(x, y, width, height)
            context.fill()
            
            context.set_source_rgb(0, 0, 0)
            self.draw_key(context, key, x + width / 4, self.height)
        
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
        gtk.Dialog.__init__(self, "Puzzle properties", palabra_window
            , gtk.DIALOG_MODAL)
        self.puzzle = puzzle
        self.set_size_request(480, 480)
        
        details = gtk.Table(1, 2, False)
        
        title_hbox = gtk.HButtonBox()
        title_hbox.set_layout(gtk.BUTTONBOX_START)
        title_hbox.pack_start(gtk.Label("Title"), False, False, 0)
        title_entry = gtk.Entry(512)
        
        def title_changed(item):
            self.puzzle.metadata["title"] = item.get_text().strip()
        title_entry.connect("changed", title_changed)
        alignment = gtk.Alignment(0, 0.5, 0, 0)
        alignment.add(gtk.Label("Title"))
        details.attach(alignment, 0, 1, 0, 1)
        details.attach(title_entry, 1, 2, 0, 1)
        
        author_hbox = gtk.HButtonBox()
        author_hbox.pack_start(gtk.Label("Author"), False, False, 0)
        author_entry = gtk.Entry(512)
        
        def author_changed(item):
            self.puzzle.metadata["author"] = item.get_text().strip()
        author_entry.connect("changed", author_changed)
        alignment = gtk.Alignment(0, 0.5, 0, 0)
        alignment.add(gtk.Label("Author"))
        details.attach(alignment, 0, 1, 1, 2)
        details.attach(author_entry, 1, 2, 1, 2)
        
        copyright_hbox = gtk.HBox(False, 0)
        copyright_hbox.pack_start(gtk.Label("Copyright"), False, False, 0)
        copyright_entry = gtk.Entry(512)
        
        def copyright_changed(item):
            self.puzzle.metadata["copyright"] = item.get_text().strip()
        copyright_entry.connect("changed", copyright_changed)
        alignment = gtk.Alignment(0, 0.5, 0, 0)
        alignment.add(gtk.Label("Copyright"))
        details.attach(alignment, 0, 1, 2, 3)
        details.attach(copyright_entry, 1, 2, 2, 3)
        
        description_hbox = gtk.HBox(False, 0)
        description_hbox.pack_start(gtk.Label("Description"), False, False, 0)
        description_entry = gtk.Entry(512)
        
        def description_changed(item):
            self.puzzle.metadata["description"] = item.get_text().strip()
        description_entry.connect("changed", description_changed)
        alignment = gtk.Alignment(0, 0.5, 0, 0)
        alignment.add(gtk.Label("Description"))
        details.attach(alignment, 0, 1, 3, 4)
        details.attach(description_entry, 1, 2, 3, 4)

        if "title" in puzzle.metadata:
            title_entry.set_text(puzzle.metadata["title"])
        if "author" in puzzle.metadata:
            author_entry.set_text(puzzle.metadata["author"])
        if "copyright" in puzzle.metadata:
            copyright_entry.set_text(puzzle.metadata["copyright"])
        if "description" in puzzle.metadata:
            description_entry.set_text(puzzle.metadata["description"])
        
        status = puzzle.grid.determine_status(True)
        
        tabs = gtk.Notebook()
        tabs.append_page(self.create_general_tab(status, puzzle), gtk.Label("General"))
        tabs.append_page(self.create_letters_tab(status, puzzle), gtk.Label("Letters"))
        
        message = self.determine_words_message(status, puzzle)
        tabs.append_page(self.create_stats_tab(message), gtk.Label("Words"))
        
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
            
        create_statistic(table, "Columns", str(puzzle.grid.width), 0, 0)
        create_statistic(table, "Rows", str(puzzle.grid.height), 0, 1)
        create_statistic(table, "Blocks", str(status["block_count"]), 0, 2)
        message = ''.join(["%.2f" % status["block_percentage"], "%"])
        create_statistic(table, "Block percentage", message, 0, 3)
        create_statistic(table, "Letters", str(status["char_count"]), 0, 4)
        create_statistic(table, "Clues", str(status["clue_count"]), 0, 5)
        
        create_statistic(table, "Checked cells", str(status["checked_count"]), 2, 0)
        create_statistic(table, "Unchecked cells", str(status["unchecked_count"]), 2, 1)
        create_statistic(table, "Total words", str(status["word_count"]), 2, 2)
        create_statistic(table, "Across words", str(status["across_word_count"]), 2, 3)
        create_statistic(table, "Down words", str(status["down_word_count"]), 2, 4)
        message = "%.2f" % status["mean_word_length"]
        create_statistic(table, "Mean word length", message, 2, 5)
        
        letters_in_use = filter(lambda (_, count): count > 0, status["char_counts_total"])
        letters_in_use_strings = map(lambda (c, _): c, letters_in_use)
        
        letters_not_in_use = filter(lambda (_, count): count == 0, status["char_counts_total"])
        letters_not_in_use_strings = map(lambda (c, _): c, letters_not_in_use)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        main.pack_start(table, False, False, 0)
        
        label = gtk.Label("Letters in use")
        label.set_alignment(0, 0)
        table.attach(label, 0, 2, 6, 7)
        label = gtk.Label(''.join(letters_in_use_strings))
        label.set_alignment(0, 0)
        table.attach(label, 2, 4, 6, 7)
        
        label = gtk.Label("Letters not in use")
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
        
        self.histogram = Histogram(status["char_counts_total"], 390, 60)
        
        for y in xrange(0, 26, 6):
            for x, (char, count) in enumerate(status["char_counts_total"][y:y + 6]):
                label = gtk.Label(''.join([char, ": ", str(count)]))
                table.attach(label, x, x + 1, y / 6, y / 6 + 1)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(6)
        main.pack_start(table, False, False, 0)
        
        def on_expose_event(drawing_area, event):
            context = drawing_area.window.cairo_create()
            self.histogram.draw(context)
            return True
        
        drawing_area = gtk.DrawingArea()
        drawing_area.set_size_request(390, 60)
        drawing_area.connect("expose_event", on_expose_event)
        
        main.pack_start(drawing_area, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        return hbox
                
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
        
    def create_letters_stats_tab(self, puzzle):
        pass
        
    @staticmethod
    def determine_general_message(status, puzzle):
        message = ''.join(
            ["Dimensions: ", str(puzzle.grid.width), " x ", str(puzzle.grid.height), "\n"
            ,"Letters: ", str(status["char_count"]), "\n"
            ,"Checked cells: ", str(status["checked_count"]), "\n"
            ,"Unchecked cells: ", str(status["unchecked_count"]), "\n"
            ,"Blocks: ", str(status["block_count"]), " (", "%.2f" % status["block_percentage"], "%)\n"
            ,"\n"
            ,"Words: ", str(status["word_count"]), "\n"
            ,"Across words: ", str(status["across_word_count"]), "\n"
            ,"Down words: ", str(status["down_word_count"]), "\n"
            ,"Clues: ", str(status["clue_count"]), "\n"
            ,"Mean word length: ", "%.2f" % status["mean_word_length"]
            ])
        return message
        
    @staticmethod
    def determine_letters_message(status, puzzle):
        count_to_str = lambda (c, count): ''.join([c, ": ", str(count), "\n"])
        message = ''.join(
            ["Letter counts:\n"
            ,''.join(map(count_to_str, status["char_counts_total"]))
            ])
        return message
        
    @staticmethod
    def determine_words_message(status, puzzle):
        word_count_to_str = lambda (length, count): ''.join([str(length), ": ", str(count), "\n"])

        message = ''.join(
            ["Word counts:\n"
            ,''.join(map(word_count_to_str, status["word_counts_total"]))
            ])
        return message
