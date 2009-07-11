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

class PropertiesWindow(gtk.Dialog):
    def __init__(self, palabra_window, puzzle):
        gtk.Dialog.__init__(self, "Puzzle properties", palabra_window
            , gtk.DIALOG_MODAL)
        self.puzzle = puzzle
        self.set_size_request(480, 420)
        
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
        word_counts = self.determine_word_counts(status, puzzle)
        char_counts = self.determine_char_counts(status, puzzle)
        message = self.determine_message(status, puzzle, word_counts, char_counts)

        text = gtk.TextView()
        text.set_editable(False)        
        data = text.get_buffer()
        data.set_text(message)
        
        scrolled_window = gtk.ScrolledWindow(None, None)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(text)
        
        main = gtk.VBox(False, 0)
        main.set_spacing(18)
        main.pack_start(details, False, False, 0)
        main.pack_start(scrolled_window, True, True, 0)
        
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(12)
        hbox.set_spacing(18)
        hbox.pack_start(main, True, True, 0)
        
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT)
        self.vbox.add(hbox)
        
    @staticmethod
    def determine_message(status, puzzle, word_counts, char_counts):
        message = ''.join(
            ["Dimensions: ", str(puzzle.grid.width), " x ", str(puzzle.grid.height), "\n"
            ,"Words: ", str(status["word_count"]), "\n"
            ,"Across words: ", str(status["across_word_count"]), "\n"
            ,"Down words: ", str(status["down_word_count"]), "\n"
            ,"Clues: ", str(status["clue_count"]), "\n"
            ,"Letters: ", str(status["char_count"]), "\n"
            ,"Checked cells: ", str(status["checked_count"]), "\n"
            ,"Unchecked cells: ", str(status["unchecked_count"]), "\n"
            ,"Blocks: ", str(status["block_count"]), " (", "%.2f" % status["block_percentage"], "%)\n"
            ,"Average word length: ", "%.2f" % status["average_word_length"], "\n"
            ,"\n"
            ,"Word counts:\n"
            ,''.join(word_counts)
            ,"\n"
            ,"Letter counts:\n"
            ,''.join(char_counts)
            ])
        return message
        
    @staticmethod
    def determine_word_counts(status, puzzle):
        word_counts = []
        for length in range(2, max(puzzle.grid.width, puzzle.grid.height) + 1):
            try:
                count = status["word_counts"][length]
            except KeyError:
                count = 0
            word_counts.append(''.join([str(length), ": ", str(count), "\n"]))
        return word_counts
        
    @staticmethod
    def determine_char_counts(status, puzzle):
        char_counts = []
        for c in map(chr, range(65, 91)):
            try:
                count = status["char_counts"][c]
            except KeyError:
                count = 0
            char_counts.append(''.join([c, ": ", str(count), "\n"]))
        return char_counts
