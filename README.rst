Script that converts text PEP into reST 

To convert a single text PEP::

   python3 restify_me.py /path/to/pep-xxx.txt
   

To go through all PEPs in python/peps/ repo::

   python3 collect_text_peps.py /path/to/peps/


current output::

   $ collect_text_peps.py ../peps/
   Found 139 PEPs still in plain text
   131 text PEPs converted :D
   Failed to reSTify 8 PEPs :(
   ../peps/pep-0100.txt because: string index out of range :(
   ../peps/pep-0227.txt because: string index out of range :(
   ../peps/pep-0236.txt because: string index out of range :(
   ../peps/pep-0308.txt because: string index out of range :(
   ../peps/pep-0324.txt because: string index out of range :(
   ../peps/pep-0343.txt because: 'Local Variables:\n' is not in list :(
   ../peps/pep-0344.txt because: string index out of range :(
   ../peps/pep-3134.txt because: string index out of range :(

