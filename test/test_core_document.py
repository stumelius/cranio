import os
import copy
import pytest
import pandas as pd
import numpy as np
import couchdb
from contextlib import suppress
from cranio.core import Document, Attachment, assert_document_equal, generate_unique_id

COUCHDB_URL = 'http://127.0.0.1:5984/'
DATABASE_NAME = 'craniodistractor'
        
@pytest.fixture
def document():
    # assing random data
    d = Document(session_id=generate_unique_id(), patient_id='test_patient',
                 data=pd.DataFrame(data=np.random.rand(100, 3), columns=list('ABC')),
                 log='abc')
    yield d
    
@pytest.fixture
def path():
    p = 'session.json'
    yield p
    with suppress(FileNotFoundError):
        os.remove(p)
        
@pytest.fixture
def couchserver():
    server = couchdb.Server(COUCHDB_URL)
    yield server
    
@pytest.fixture
def db(couchserver):
    try:
        db = couchserver[DATABASE_NAME]
    except couchdb.http.ResourceNotFound:
        db = couchserver.create(DATABASE_NAME)
    yield db
        
def test_Document_init_with_required_arguments():
    document = Document(session_id='foo', patient_id='123')
    assert document._id is not None
    assert document.session_id is 'foo'
    assert document.patient_id is '123'
    # no arguments
    with pytest.raises(TypeError):
        Document()

def test_Document_save_and_load(document, path):
    document.save(path)
    d2 = Document.load(path)
    assert document.as_document() == d2.as_document()
    
def test_Document_data_and_log_io(document):
    # verify data integrity after reading from io object
    with document.data_io() as dio:
        df = pd.read_csv(dio, sep=';', index_col=0)
    pd.testing.assert_frame_equal(df, document.data)
    # verify log integrity after reading from io object
    with document.log_io() as lio:
        assert lio.read() == document.log

@pytest.mark.couchdb
def test_Document_to_couchdb(db, document):
    doc = document.as_document()
    doc_id, rev_id = db.save(doc)
    # put attachments
    for attachment in document.attachments():
        db.put_attachment(db[doc_id], **attachment._asdict())
    # read attachments and verify contents
    for attachment in document.attachments():
        bytesio = db.get_attachment(doc_id, attachment.filename)
        assert bytesio.read().decode() == attachment.content
    # delete document
    db.delete(db[doc_id])

def test_assert_document_equal(document):
    doc1 = document.as_document()
    doc2 = copy.copy(doc1)
    assert_document_equal(doc1, doc2)
    # change id
    doc2['_id'] = '123'
    with pytest.raises(AssertionError):
        assert_document_equal(doc1, doc2)
    # change id back to original
    doc2['_id'] = doc1['_id']
    assert_document_equal(doc1, doc2)
    # add new field
    doc2['new_field'] = 'abc'
    with pytest.raises(AssertionError):
        assert_document_equal(doc1, doc2)
    # delete new field
    del doc2['new_field']
    assert_document_equal(doc1, doc2)
    # add attachments
    doc2['_attachments'] = {'name': 'data.csv'}
    with pytest.raises(AssertionError):
        assert_document_equal(doc1, doc2)
    assert_document_equal(doc1, doc2, check_attachments=False)
    # remove attachments
    del doc2['_attachments']
    assert_document_equal(doc1, doc2)
    # add revision
    doc2['_rev'] = '123'
    with pytest.raises(AssertionError):
        assert_document_equal(doc1, doc2)
    assert_document_equal(doc1, doc2, check_rev=False)
    # remove revision
    del doc2['_rev']
    assert_document_equal(doc1, doc2)
    
@pytest.mark.couchdb
def test_Document_client_side_update_handler(db, document):
    # create original document
    doc = document.as_document()
    doc_id, rev_id = db.save(doc)
    # put attachments
    for attachment in document.attachments():
        db.put_attachment(db[doc_id], **attachment._asdict())
    # retrieve document from database
    doc_ret = db[doc_id]
    # document contents are equal except for the attachments and revision
    assert_document_equal(doc, doc_ret, check_attachments=False, check_rev=False)
    with pytest.raises(AssertionError):
        assert_document_equal(doc, doc_ret)    
    # delete document
    db.delete(db[doc_id])