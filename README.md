[![Build Status](https://github.com/davidbrochart/ypywidgets/workflows/test/badge.svg)](https://github.com/davidbrochart/ypywidgets/actions)

# ypywidgets: Y-based Jupyter widgets for Python

`ypywidgets` is a communication backend between a Jupyter kernel and clients. It allows to synchronize data structures that can be modified concurrently, and automatically resolves conflicts. To do so, it uses:
- the Jupyter kernel [Comm](https://jupyter-client.readthedocs.io/en/stable/messaging.html#custom-messages) protocol as the transport layer, and the [comm](https://github.com/ipython/comm) implementation of it.
- the [pycrdt](https://github.com/davidbrochart/pycrdt) CRDT implementation.
- the [declare](https://github.com/willmcgugan/declare) library that implements the observer pattern and validation.

It is a replacement for (a part of) [ipywidgets](https://ipywidgets.readthedocs.io). When used with [yjs-widgets](https://github.com/davidbrochart/yjs-widgets), it supports JupyterLab clients that implement widgets. The difference with `ipywidgets` is that these widgets are collaborative: they can be manipulated concurrently from the kernel or from any client. The CRDT algorithm ensures that a widget state will eventually be consistent across all clients.
