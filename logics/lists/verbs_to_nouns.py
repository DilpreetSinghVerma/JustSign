def verbToNoun(verb):
  verbNouns = {
    "lose":"losing",
    "suspend":"suspension",
  }
  return verbNouns.get(verb,verb)