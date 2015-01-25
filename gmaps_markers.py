#coding: utf-8
#!/usr/bin/env python

"""
    This project:
        1. Opens PyQt window with:
            a) six text fields:
                - markers source (file or http)
                - item's name
                - item's address
                - item's latitude 
                - item's longtitude
                - other (comments/remarks etc)
            b) google map with those fields marked
            c) go button ;]
        2. Select data regarding selected marker in listview, write data to fields.
        3. Might in future allow to delete/add marker

        Authored K.Królczyk (6h), 2015-01-25 (Happy birthday Sis!), MIT License, ver:0.7
"""

import os
import sys
#import gdata.docs.service
import qgmap                        # pip install qgmap    | GNU License...
# sudo cp -r /usr/local/lib/python3.2/dist-packages/qgmap /usr/local/lib/python2.7/dist-packages/qgmap
# sudo vim /usr/local/lib/python2.7/dist-packages/qgmap/__init__.py => usePySide=False
import gdata.spreadsheet.service    # pip install gdata
from xml.etree import ElementTree   # pip install ...something, cant remember
from PyQt4 import QtGui, QtCore     # sudo apt get install python-qt4 qt4-dev-tools

def run_application(markers):
    
    list_of_markers, source = load(markers)
    if not list_of_markers:
        print("No markers have been loaded.")
        #list_of_markers = [len(Entry.fields)*[[]]]
        list_of_markers = []
    else:
        print("%d markers have been loaded." %len(list_of_markers))

    app = QtGui.QApplication([])
    runme = Layout(list_of_markers, source)
    runme(app)

def load(path_or_http):
    """ Google map marker values reader """
    if not path_or_http:
        return None
    else:
        try:
            return FileHandler(path_or_http).get_rows(), path_or_http
        except TypeError:
            pass
        except (OSError, IOError) as err:
            print err
        try:
            return GoogleDocsHandler(*path_or_http).get_rows()
        except TypeError:
            pass


class Layout(QtGui.QWidget):
    def __call__(self, app):
        #self.showFullScreen()
        #self.show()
        self.showMaximized()
        app.exec_()
    def __init__(self, prepared_rows, src):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle("Pubs tracker. Where do You want to drink today?")
        self.source = src
        self.layout = QtGui.QVBoxLayout()
        self.populate_layout(prepared_rows)
        self.setLayout(self.layout)
    #def sizeHint(self): return QtCore.QSize(1024, 800)
    def populate_layout(self, rows):
        self.display_fields = Entry(rows)
        self.layout.addWidget(self.display_fields)
        self.layout.addStretch(1)

        # TODO: move to class
        self.gmap = qgmap.QGoogleMap(self)
        self.gmap.waitUntilReady()
        self.gmap.centerAt(52.2176, 21.01574)
        self.gmap.setZoom(17)
        self.gmap.mapMoved.connect(self.map_info)
        self.gmap.markerMoved.connect(self.map_info)
        self.gmap.mapClicked.connect(self.map_info)
        self.gmap.mapDoubleClicked.connect(self.map_info)
        self.gmap.mapRightClicked.connect(self.map_info)
        self.gmap.markerClicked.connect(self.map_info)
        self.gmap.markerDoubleClicked.connect(self.map_info)
        self.gmap.markerRightClicked.connect(self.map_info)

        for row in rows:
            if not row:
                continue
            self.gmap.addMarker(row[0], row[2], row[3], **dict(
            icon="http://google.com/mapfiles/ms/micons/blue-dot.png",
            draggable=True,
            title = row[1] + " <br> " +row[4]))

        self.layout.addWidget(self.gmap)
        
        self.layout.addStretch(1)
        self.source_text = QtGui.QLineEdit()
        self.source_text.setText(self.source)
        self.layout.addWidget(self.source_text)
        self.refresh_button = QtGui.QPushButton("Refresh (todo)")
        #self.refresh_button.connect() #  "i should refresh markers."
        self.layout.addWidget(self.refresh_button)

    def map_info(self, name=None, lon=None, lat=None):
        print (name, lon, lat)

        if isinstance(lon, float) and lat is None:
            name, lat = "when..what?", name
        addr, szer, dlug, info = "where?", str(lon), str(lat), "not impl ;]"
        self.display_fields.edit((name, addr, szer, dlug, info))

# class Gmap(QtGui.QDialog):
# TODO: this.
#     def  __init__(self):
#         QtGui.QDialog.__init__(self)
#     def __call__(self):
#         self.gmap = qgmap.QGoogleMap(self)
#         self.addWidget(self.gmap)
     # def add_marker(self, place):
     #    self.addMarkerAtAddress(place,
     #    icon="http://google.com/mapfiles/ms/micons/green-dot.png")
        #     self.gmap.addMarkerAtAddress(place,
        #         icon="http://google.com/mapfiles/ms/micons/green-dot.png")
        #self.gmap.centerAtAddress("Armii Ludowej, Warszawa")
        #self.gmap.setSizePolicy(
        #     QtGui.QSizePolicy.MinimumExpanding,
        #     QtGui.QSizePolicy.MinimumExpanding)


class Entry(QtGui.QWidget):
    """ if in distant future i'd like to display and edit table... i'll need it """
    fields = ("Name", "Address", "Lat", "Long", "Comments")
    def __init__(self, row):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout()
        self.populate_fields(row)
        self.setLayout(self.layout)

    def edit(self, values):
        for key, val in zip(self.fields, values):
            getattr(self, key).setText(str(val))

    def populate_fields(self, row):
        for item in self.fields:
            setattr(self, item, QtGui.QLineEdit(self))
            getattr(self, item).setPlaceholderText(item)
            self.layout.addWidget(getattr(self, item))

class FileHandler(object):
    """ Row consist of: name, address, longtitude, latitude, comments """
    def __init__(self, path):
        with open(path, 'r') as _file:
            self.rows = [ row.strip().split(";") for row in _file ]
    def get_rows(self):
        #strip header row
        return self.rows[1:]

class GoogleDocsHandler(object):
    """ Handles google spreadsheet (barely) """
    def __init__(self, key, worksheet_id, visibility, projection):
        self.client = gdata.spreadsheet.service.SpreadsheetsService()
        #self.client2 = gdata.docs.service.DocsService()
        #user, pass = 'krzysztof.krolczyk@github.com', 'a_Password_OBVIOUSLY'
        #self.client2.ClientLogin(user, pass)
        #self.client3 = gdata.spreadsheet.text_db.DatabaseClient()
        #self.client3.GetDatabases(name="MySsreadsheetName")
        #self.worksheets = self.client.GetWorksheetsFeed(key)
        gcells = self.client.GetCellsFeed(key, 
                                          wksht_id=worksheet_id, 
                                          visibility=visibility, 
                                          projection=projection)
        # cast SpreadsheetsCellsFeed into some sane iterable list
        self.cells = [cell.content.text for cell in gcells.entry]
        # locations = [cell.title.text for cell in gcells.entry]
        self.src = "http://docs.google.com/spreadsheets/d/" + key

    def get_rows(self):
        """ Row consist of: name, address, longtitude, latitude, comments """
        # could use regex here to differentiate col/row from AB201
        # but actually suppose we will never need as much cols/rows
        cols_limit = len(Entry.fields)
        rows_limit = 10 # including header
        new_row = cols_limit * rows_limit
        rows = [ self.cells[splice:splice+cols_limit] # : -1 ?  
                 for splice in range(0, cols_limit*rows_limit, cols_limit) ]
        # strip first row (header)
        return rows[1:], self.src
        # TODO: stipping also last row, for some reason google docs seem to append empty?

    def _PrintFeed(self, feed):
        """ from google docs """
        for i, entry in enumerate(feed.entry):
          if isinstance(feed, gdata.spreadsheet.SpreadsheetsCellsFeed):
            print 'SpreadsheetsCellsFeed %s %s' % (entry.title.text, entry.content.text)
          elif isinstance(feed, gdata.spreadsheet.SpreadsheetsListFeed):
            print 'SpreadsheetsListFeed %s %s %s' % (i, entry.title.text, entry.content.text)
            # Print this row's value for each column (the custom dictionary is
            # built using the gsx: elements in the entry.)
            print 'Contents:'
            for key in entry.custom:
              print 'sth  %s: %s' % (key, entry.custom[key].text) 
          else:
            print 'htw %s %s\n' % (i, entry.title.text)

class Tests(object):

    @staticmethod
    def test_file():
        return "/tmp/showmethewaytothenextwhiskeybaar"

    @staticmethod
    def test_file2():
        import cStringIO
        output = cStringIO.StringIO()
        output.write("name;address;lat;long;comment \n"
                     "aa;zupa1;1.2;3.4;aacoment     \n"
                     "bb;pupa2;7.7;69.69;bbcomment  \n"
                     "cc;lupa3;3.14;66.6;cccomment  \n")
        return output

    @staticmethod
    def test_http():
        # 1. document must be PUBLISHED on the web, not just "public"
        # random google spreadsheet key
        key = "1lzJYiUAxDdWfuJGCrFNn3wNCe5x-aG5Q7TG8hESzn6Y" #/pub?key=
        # google base address
        base = "http://docs.google.com/spreadsheets/d/"
        #base2 = "spreadsheets.google.com"
        nologin = "&ndplr=1"
        wksht_id = "od6"    #nice, Google, very classy.
        visibility="public"
        projection="basic"
        #return base+key+nologin
        return key, wksht_id, visibility, projection

    @staticmethod
    def normal_operation():
        return None

if __name__ == "__main__":
    default = Tests.test_http()
    run_application(sys.argv[1:] or default)