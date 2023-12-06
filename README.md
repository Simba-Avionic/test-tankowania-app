# test-tankowania-app

# Można to wykorzystać jako baze do aplikacji do silnika


## TODO:
* ### Skopiowanie aplikacji z RPI
* Wyizololowanie kodu SOME/IP od kodu aplikacji(Moze osobne repo? SOME/IP Python)
* Dodanie ustawień:
  * przelicznik dla ADC.
  * adres ip servera,
  * lokalny adres ip (funkcja get_local_ip, zastanowić się nad hostem do którego sie odwoływać w celu ustawienia ip, może pobierać z ustawień systemu?), 
  * czas odswiezania danych na ekranie,
* Zbudowanie aplikacji:
  * windows
  * linux
  * android/web
* stworzenie github actions które po merge do master zbuduje wersje dla wszystkich systemów