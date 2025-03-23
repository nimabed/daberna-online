import game_pb2

class GameSerialization:
    @staticmethod
    def serialize(game):
        game_proto = game_pb2.Game()
        game_proto.players.extend(game.players)
        for move_list in game.moves:
            move_list_proto = game_pb2.MovesList()
            for move in move_list:
                move_proto = game_pb2.Tuple()
                move_proto.first, move_proto.second = move
                move_list_proto.move.append(move_proto)
            game_proto.moves.append(move_list_proto)
        game_proto.result.extend(game.result)
        game_proto.running = game.running
        game_proto.reset_var = game.reset_var
        game_proto.rand_num = game.rand_num if game.rand_num is not None else 0
        game_proto.start_counter = game.start_counter
        game_proto.random_num_counter = game.random_num_counter
        return game_proto.SerializeToString()
    
    @staticmethod
    def deserialize(game_bytes):
        game_proto = game_pb2.Game()
        game_proto.ParseFromString(game_bytes)
        game = {
            "players": list(game_proto.players),
            "moves": [[(move.first,move.second) for move in move_list.move]for move_list in game_proto.moves],
            "result": list(game_proto.result),
            "running": game_proto.running,
            "reset_var": game_proto.reset_var,
            "rand_num": game_proto.rand_num if game_proto.rand_num != 0 else None,
            "start_counter": game_proto.start_counter,
            "random_num_counter": game_proto.random_num_counter
        }
        return game

    @staticmethod
    def serialize_cards(cards_data):
        proto_dict = game_pb2.DictCards()
        for player, cards in cards_data.items():
            proto_cards = game_pb2.OuterList()
            for card in cards:
                proto_card = game_pb2.InnerList()
                for item in card:
                    proto_item = game_pb2.InnerInner()
                    proto_item.values.extend(item)
                    proto_card.lists.append(proto_item)
                proto_cards.cards.append(proto_card)
            proto_dict.gamedict[player].CopyFrom(proto_cards)
        return proto_dict.SerializeToString()
    
    @staticmethod
    def deserialize_cards(data_bytes):
        proto_dict = game_pb2.DictCards()
        proto_dict.ParseFromString(data_bytes)
        deserialized_dict = {}
        for player, cards in proto_dict.gamedict.items():
            deserialized_dict[player] = []
            for innerlist in cards.cards:
                inner = [list(item.values) for item in innerlist.lists]
                deserialized_dict[player].append(inner)
        return deserialized_dict