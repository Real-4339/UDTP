# Bugs

```powershell
  Available IPs: ['192.168.56.1', '192.168.50.177', '127.0.0.1']
  IP >>> 192.168.50.177
  Port range: 49152 - 65535
  Port >>> 50000
  Successfully binded , so ip and port are available
  DEBUG:Host:Host registered on 192.168.50.177:50000
  Try 'help' >>> connect 192.168.50.177:65000
  Starting connection to 192.168.50.177:65000
  Traceback (most recent call last):
    File "<frozen runpy>", line 198, in _run_module_as_main
  Try 'help' >>>   File "<frozen runpy>", line 88, in _run_code
    File "C:\Users\vadti\OneDrive\Documents\PKS\zadanie_2\R-UDP\protocol\__main__.py", line 101, in <module>
      main()
    File "C:\Users\vadti\OneDrive\Documents\PKS\zadanie_2\R-UDP\protocol\__main__.py", line 93, in main
      host.run()
    File "C:\Users\vadti\OneDrive\Documents\PKS\zadanie_2\R-UDP\protocol\host.py", line 233, in run
      self._endless_loop()
    File "C:\Users\vadti\OneDrive\Documents\PKS\zadanie_2\R-UDP\protocol\host.py", line 191, in _endless_loop
      self._v4()
    File "C:\Users\vadti\OneDrive\Documents\PKS\zadanie_2\R-UDP\protocol\host.py", line 179, in _v4
      result = iterator()
              ^^^^^^^^^^
    File "C:\Users\vadti\OneDrive\Documents\PKS\zadanie_2\R-UDP\protocol\host.py", line 145, in _iterator
      data, addr = self.__socket.recvfrom(1472)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
```

1) Explanation, Unix:
   I ignore spoofed packets, but only based on ip, mb should check for both.
   Windows:
   Idk, need to check wireshark.

2) Free update

3) error simulation, only packet corruption

4) Seems packets are send one by one, not in range

5) WM

6) Terminal: Proper input validation (new message, min)

7) IP header 60 bytes, have to check and mb dynamicly change MTU.

8) Can not connect Windows and linux VM. (I think because of old spoofing check)

# Done

- Keep alive