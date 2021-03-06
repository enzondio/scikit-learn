"""
General tests for all estimators in sklearn.
"""
import os
import warnings
import sys
import traceback

import numpy as np
from scipy import sparse
from nose.tools import assert_raises, assert_equal
from numpy.testing import assert_array_equal

import sklearn
from sklearn.utils.testing import all_estimators
from sklearn.utils.testing import assert_greater
from sklearn.base import clone, ClassifierMixin, RegressorMixin, \
        TransformerMixin
from sklearn.utils import shuffle
from sklearn.preprocessing import Scaler
#from sklearn.cross_validation import train_test_split
from sklearn.datasets import load_iris, load_boston
from sklearn.metrics import zero_one_score
from sklearn.lda import LDA
from sklearn.svm.base import BaseLibSVM

# import "special" estimators
from sklearn.grid_search import GridSearchCV
from sklearn.decomposition import SparseCoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import BaseEnsemble
from sklearn.multiclass import OneVsOneClassifier, OneVsRestClassifier,\
        OutputCodeClassifier
from sklearn.feature_selection import RFE, RFECV
from sklearn.naive_bayes import MultinomialNB, BernoulliNB
from sklearn.covariance import EllipticEnvelope, EllipticEnvelop
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import LabelBinarizer, LabelEncoder

dont_test = [Pipeline, GridSearchCV, SparseCoder, EllipticEnvelope,
        EllipticEnvelop, DictVectorizer, LabelBinarizer, LabelEncoder]
meta_estimators = [BaseEnsemble, OneVsOneClassifier, OutputCodeClassifier,
        OneVsRestClassifier, RFE, RFECV]


def test_all_estimators():
    # Test that estimators are default-constructible, clonable
    # and have working repr.
    estimators = all_estimators()
    clf = LDA()

    for name, E in estimators:
        # some can just not be sensibly default constructed
        if E in dont_test:
            continue
        # test default-constructibility
        # get rid of deprecation warnings
        with warnings.catch_warnings(record=True):
            if E in meta_estimators:
                e = E(clf)
            else:
                e = E()
            #test cloning
            clone(e)
            # test __repr__
            repr(e)


def test_estimators_sparse_data():
    # All estimators should either deal with sparse data, or raise an
    # intelligible error message
    rng = np.random.RandomState(0)
    X = rng.rand(40, 10)
    X[X < .8] = 0
    X = sparse.csr_matrix(X)
    y = (4 * rng.rand(40)).astype(np.int)
    estimators = all_estimators()
    estimators = [(name, E) for name, E in estimators
                        if issubclass(E, (ClassifierMixin, RegressorMixin))]
    for name, Clf in estimators:
        if Clf in dont_test or Clf in meta_estimators:
            continue
        # catch deprecation warnings
        with warnings.catch_warnings(record=True):
            clf = Clf()
        # fit
        try:
            clf.fit(X, y)
        except TypeError, e:
            if not 'sparse' in repr(e):
                print ("Estimator %s doesn't seem to fail gracefully on "
                    "sparse data" % name)
                traceback.print_exc(file=sys.stdout)
                raise e
        except Exception, exc:
            print ("Estimator %s doesn't seem to fail gracefully on "
                "sparse data" % name)
            traceback.print_exc(file=sys.stdout)
            raise exc


def test_transformers_sparse_data():
    # All estimators should either deal with sparse data, or raise an
    # intelligible error message
    rng = np.random.RandomState(0)
    X = rng.rand(40, 10)
    X[X < .8] = 0
    X = sparse.csr_matrix(X)
    y = (4 * rng.rand(40)).astype(np.int)
    estimators = all_estimators()
    estimators = [(name, E) for name, E in estimators
                        if issubclass(E, TransformerMixin)]
    for name, Trans in estimators:
        if Trans in dont_test or Trans in meta_estimators:
            continue
        # catch deprecation warnings
        with warnings.catch_warnings(record=True):
            if Trans is Scaler:
                trans = Trans(with_mean=False)
            else:
                trans = Trans()
        # fit
        try:
            trans.fit(X, y)
        except TypeError, e:
            if not 'sparse' in repr(e):
                print ("Estimator %s doesn't seem to fail gracefully on "
                    "sparse data" % name)
                traceback.print_exc(file=sys.stdout)
                raise e
        except Exception, exc:
            print ("Estimator %s doesn't seem to fail gracefully on "
                "sparse data" % name)
            traceback.print_exc(file=sys.stdout)
            raise exc


def test_classifiers_one_label():
    # test classifiers trained on a single label always return this label
    # or raise an sensible error message
    rnd = np.random.RandomState(0)
    X_train = rnd.uniform(size=(10, 3))
    X_test = rnd.uniform(size=(10, 3))
    y = np.ones(10)
    estimators = all_estimators()
    classifiers = [(name, E) for name, E in estimators if issubclass(E,
        ClassifierMixin)]
    error_string_fit = "Classifier can't train when only one class is present."
    error_string_predict = ("Classifier can't predict when only one class is "
        "present.")
    for name, Clf in classifiers:
        if Clf in dont_test or Clf in meta_estimators:
            continue
        # catch deprecation warnings
        with warnings.catch_warnings(record=True):
            clf = Clf()
            # try to fit
            try:
                clf.fit(X_train, y)
            except ValueError, e:
                if not 'class' in repr(e):
                    print(error_string_fit, Clf, e)
                    traceback.print_exc(file=sys.stdout)
                    raise e
                else:
                    continue
            except Exception, exc:
                    print(error_string_fit, Clf, exc)
                    traceback.print_exc(file=sys.stdout)
                    raise exc
            # predict
            try:
                assert_array_equal(clf.predict(X_test), y)
            except Exception, exc:
                print(error_string_predict, Clf, exc)
                traceback.print_exc(file=sys.stdout)


def test_classifiers_train():
    # test if classifiers do something sensible on training set
    # also test all shapes / shape errors
    estimators = all_estimators()
    classifiers = [(name, E) for name, E in estimators if issubclass(E,
        ClassifierMixin)]
    iris = load_iris()
    X, y = iris.data, iris.target
    X, y = shuffle(X, y, random_state=7)
    n_samples, n_features = X.shape
    n_labels = len(np.unique(y))
    X = Scaler().fit_transform(X)
    for name, Clf in classifiers:
        if Clf in dont_test or Clf in meta_estimators:
            continue
        if Clf in [MultinomialNB, BernoulliNB]:
            # TODO also test these!
            continue
        # catch deprecation warnings
        with warnings.catch_warnings(record=True):
            clf = Clf()
        # raises error on malformed input for fit
        assert_raises(ValueError, clf.fit, X, y[:-1])

        # fit
        clf.fit(X, y)
        y_pred = clf.predict(X)
        assert_equal(y_pred.shape, (n_samples,))
        # training set performance
        assert_greater(zero_one_score(y, y_pred), 0.78)

        # raises error on malformed input for predict
        assert_raises(ValueError, clf.predict, X.T)
        if hasattr(clf, "decision_function"):
            try:
                # decision_function agrees with predict:
                decision = clf.decision_function(X)
                assert_equal(decision.shape, (n_samples, n_labels))
                # raises error on malformed input
                assert_raises(ValueError, clf.decision_function, X.T)
                if not isinstance(clf, BaseLibSVM):
                    # 1on1 of LibSVM works differently
                    assert_array_equal(np.argmax(decision, axis=1), y_pred)
                # raises error on malformed input for decision_function
                assert_raises(ValueError, clf.decision_function, X.T)
            except NotImplementedError:
                pass
        if hasattr(clf, "predict_proba"):
            try:
                # predict_proba agrees with predict:
                y_prob = clf.predict_proba(X)
                assert_equal(y_prob.shape, (n_samples, n_labels))
                # raises error on malformed input
                assert_raises(ValueError, clf.predict_proba, X.T)
                assert_array_equal(np.argmax(y_prob, axis=1), y_pred)
                # raises error on malformed input for predict_proba
                assert_raises(ValueError, clf.predict_proba, X.T)
            except NotImplementedError:
                pass


def test_classifiers_classes():
    # test if classifiers can cope with non-consecutive classes
    estimators = all_estimators()
    classifiers = [(name, E) for name, E in estimators if issubclass(E,
        ClassifierMixin)]
    iris = load_iris()
    X, y = iris.data, iris.target
    X, y = shuffle(X, y, random_state=7)
    X = Scaler().fit_transform(X)
    y = 2 * y + 1
    # TODO: make work with next line :)
    #y = y.astype(np.str)
    for name, Clf in classifiers:
        if Clf in dont_test or Clf in meta_estimators:
            continue
        if Clf in [MultinomialNB, BernoulliNB]:
            # TODO also test these!
            continue

        # catch deprecation warnings
        with warnings.catch_warnings(record=True):
            clf = Clf()
        # fit
        clf.fit(X, y)
        y_pred = clf.predict(X)
        # training set performance
        assert_array_equal(np.unique(y), np.unique(y_pred))
        assert_greater(zero_one_score(y, y_pred), 0.78)


def test_regressors_train():
    estimators = all_estimators()
    regressors = [(name, E) for name, E in estimators if issubclass(E,
        RegressorMixin)]
    boston = load_boston()
    X, y = boston.data, boston.target
    X, y = shuffle(X, y, random_state=0)
    # TODO: test with intercept
    # TODO: test with multiple responses
    X = Scaler().fit_transform(X)
    y = Scaler().fit_transform(y)
    for name, Reg in regressors:
        if Reg in dont_test or Reg in meta_estimators:
            continue
        # catch deprecation warnings
        with warnings.catch_warnings(record=True):
            reg = Reg()
        if hasattr(reg, 'alpha'):
            reg.set_params(alpha=0.01)

        # raises error on malformed input for fit
        assert_raises(ValueError, reg.fit, X, y[:-1])
        # fit
        reg.fit(X, y)
        reg.predict(X)
        assert_greater(reg.score(X, y), 0.5)


def test_configure():
    # Smoke test the 'configure' step of setup, this tests all the
    # 'configure' functions in the setup.pys in the scikit
    cwd = os.getcwd()
    setup_path = os.path.abspath(os.path.join(sklearn.__path__[0], '..'))
    setup_filename = os.path.join(setup_path, 'setup.py')
    if not os.path.exists(setup_filename):
        return
    try:
        os.chdir(setup_path)
        old_argv = sys.argv
        sys.argv = ['setup.py', 'config']
        with warnings.catch_warnings():
            # The configuration spits out warnings when not finding
            # Blas/Atlas development headers
            warnings.simplefilter('ignore',  UserWarning)
            execfile('setup.py', dict(__name__='__main__'))
    finally:
        sys.argv = old_argv
        os.chdir(cwd)
