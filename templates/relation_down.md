class $toTable{
      $toColumn
    }
    $fromTable "*" <|--$crossFilteringBehavior $toTable "$toCardinality":$fromColumn
    link $toTable "$link"