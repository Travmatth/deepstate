from __future__ import print_function
from unittest import TestCase


class DeepStateTestCase(TestCase):
  def test_angr(self):
    self.run_deepstate("deepstate-angr")

  def test_manticore(self):
    self.run_deepstate("deepstate-manticore")

  def run_deepstate(self, deepstate):
    raise NotImplementedError("Define an actual test of DeepState in DeepStateTestCase:run_deepstate.")


class DeepStateFuzzerTestCase(TestCase):
  def test_afl(self):
    self.run_deepstate("deepstate-afl")

  def test_libfuzzer(self):
    self.run_deepstate("deepstate-libfuzzer")

  def test_honggfuzz(self):
    self.run_deepstate("deepstate-honggfuzz")

  def test_angora(self):
    self.run_deepstate("deepstate-angora")

  def test_eclipser(self):
    self.run_deepstate("deepstate-eclipser")

  def run_deepstate(self, deepstate):
    raise NotImplementedError("Define an actual test of DeepState in DeepStateFuzzerTestCase:run_deepstate.")
