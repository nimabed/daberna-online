import game_pb2

class Game:
    def __init__(self, num_of_players):
        self.players = ["" for i in range(num_of_players)]
        self.moves = [[] for i in range(num_of_players)]
        self.result = [0 for i in range(num_of_players)]
        self.players_num = num_of_players
        self.running = False
        self.rand_num = None
        self.start_counter = 4
        self.random_num_counter = 9


    def all_connected(self):
        return all(self.players)   

    # Added with NARENJAK! :-)
    def reset(self):
        self.moves = [[] for i in range(self.players_num)]
        self.result = [0 for i in range(self.players_num)]
        self.start_counter = 4
        
    def player_move(self, p_id, number):
        self.moves[p_id].append(tuple(number.split(",")))

    def winner_check(self, p_id, cards):
        check_list = self.moves[p_id]

        for index, card in enumerate(cards):
            for i in range(3):
                if [True for item in card if item[i].isdigit()] == [True for item in card if (item[i], str(index)) in check_list]:
                    self.result[p_id] = 1
                    return 
            
    def serialize(self):
        game_proto = game_pb2.Game()
        game_proto.players.extend(self.players)
        for move_list in self.moves:
            move_list_proto = game_pb2.MovesList()
            for move in move_list:
                move_proto = game_pb2.Tuple()
                move_proto.first, move_proto.second = move
                move_list_proto.move.append(move_proto)
            game_proto.moves.append(move_list_proto)
        game_proto.result.extend(self.result)
        game_proto.running = self.running
        game_proto.rand_num = self.rand_num if self.rand_num is not None else 0
        game_proto.start_counter = self.start_counter
        game_proto.random_num_counter = self.random_num_counter

        return game_proto.SerializeToString()

    def deserialize(self, data):
        game_proto = game_pb2.Game()
        game_proto.ParseFromString(data)
        self.players = list(game_proto.players)
        self.moves = [[(move.first,move.second) for move in move_list.move]for move_list in game_proto.moves]
        self.result = list(game_proto.result)
        self.running = game_proto.running
        self.rand_num = game_proto.rand_num if game_proto.rand_num != 0 else None
        self.start_counter = game_proto.start_counter
        self.random_num_counter = game_proto.random_num_counter

    def serialize_cards(self, the_dict):
        proto_dict = game_pb2.DictCards()

        for player, cards in the_dict.items():
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
    
    def deserialize_cards(self, serialized_data):
        proto_dict = game_pb2.DictCards()
        proto_dict.ParseFromString(serialized_data)

        deserialized_dict = {}
        for player, cards in proto_dict.gamedict.items():
            deserialized_dict[player] = []
            for innerlist in cards.cards:
                inner = []
                for item in innerlist.lists:
                    inner.append(list(item.values))
                deserialized_dict[player].append(inner)

        return deserialized_dict


        
            
            

        
    

        
    
        
    
    

