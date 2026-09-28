def minimax(node, depth, maximizing_player):
    if type(node) == int or depth == 0:  # Terminal
        return node

    if maximizing_player == True:
        best_value = float("-inf")

        for child in node:
            value = minimax(child, depth - 1, False)
            best_value = max(best_value, value)

        return best_value

    else:
        best_value = float("inf")

        for child in node:
            value = minimax(child, depth - 1, True)
            best_value = min(best_value, value)

        return best_value


def build_tree(n: int, depth: int = 0):
    if n == 1:
        terminals = []
        nt = int(
            input(
                f"\033[32mEnter number of terminal values for layer ({depth})\033[0m: "
            )
        )
        for i in range(nt):
            terminals.append(
                int(input(f"\033[31mEnter terminal value ({i + 1})\033[0m: "))
            )
        print()

        return terminals

    tree = []
    nt = int(
        input(
            f"\033[34mEnter the number of nodes for layer {depth} ({'Max' if depth % 2 == 0 else 'Min'})\033[0m: "
        )
    )

    for _ in range(nt):
        tree.append(build_tree(n - 1, depth + 1))

    return tree


def main():
    n = int(input("Enter Number of Layers of the tree: "))
    print()
    tree = build_tree(n, 0)
    print(tree)

    result = minimax(tree, 3, True)
    print("Minimax value:", result)


if __name__ == "__main__":
    main()
