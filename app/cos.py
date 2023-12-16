from  SomeIPHeader import SomeIPHeader
import struct
from SomeIPSocket import SomeIpSocket
import datetime
import csv
import threading
from config import Config
import flet
from flet import Page,Row,TextButton,TextField
import time
import logging
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from data import Data,PlotData

async def main(page:Page):
    page.title="Engine test app"
    page.vertical_alignment="center"
    while True:           
        await page.add_async(
        Row([
            TextField(label="vo",width=40),
            TextButton("Open valve"),
            TextButton("Close valve")

        ])
        )
        await page.add_async(flet.DataTable(
            columns=[
                flet.DataColumn(flet.Text("name")),
                flet.DataColumn(flet.Text("value"),numeric=True)
            ],
            rows=[
                flet.DataRow(
                    cells=[
                        flet.DataCell(flet.Text("pressure")),
                        flet.DataCell(flet.Text(12))
                    ]
                ),
                flet.DataRow(
                    cells=[
                        flet.DataCell(flet.Text("temp")),
                        flet.DataCell(flet.Text(13))
                    ]
                ),
                flet.DataRow(
                    cells=[
                        flet.DataCell(flet.Text("A1")),
                        flet.DataCell(flet.Text(14))
                    ]
                ),
                flet.DataRow(
                    cells=[
                        flet.DataCell(flet.Text("tenso")),
                        flet.DataCell(flet.Text(15))
                    ]
                ),
                                    flet.DataRow(
                    cells=[
                        flet.DataCell(flet.Text("temp góra")),
                        flet.DataCell(flet.Text(16))
                    ]
                ),
                flet.DataRow(
                    cells=[
                        flet.DataCell(flet.Text("temp środek")),
                        flet.DataCell(flet.Text(18))
                    ]
                ),
                flet.DataRow(
                    cells=[
                        flet.DataCell(flet.Text("tmp dół")),
                        flet.DataCell(flet.Text(20))
                    ]
                )
            ]
        ))
        time.sleep(1)
        page.clean()

flet.app(main)